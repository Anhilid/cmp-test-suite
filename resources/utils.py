# SPDX-FileCopyrightText: Copyright 2024 Siemens AG
#
# SPDX-License-Identifier: Apache-2.0

"""Utilities for various tasks and a place to store functions that do not belong elsewhere."""

import base64
import logging
import os
import re
import textwrap
from base64 import b64decode, b64encode
from collections import Counter
from itertools import combinations
from typing import Any, Iterable, List, Optional, Tuple, Union

from pq_logic.hybrid_structures import CompositeSignatureValue
from pyasn1.codec.der import decoder, encoder
from pyasn1.type import base, univ
from pyasn1_alt_modules import rfc2986, rfc5280, rfc6402, rfc9480
from robot.api.deco import keyword, not_keyword

from resources import certutils, keyutils
from resources.oidutils import PYASN1_CM_NAME_2_OIDS
from resources.typingutils import PrivateKey, Strint


def nonces_must_be_diverse(nonces: List[bytes], minimal_hamming_distance: Strint = 10):
    """Check that a list of nonces are diverse enough, by computing the Hamming distance between them.

    Nonces will be right-padded with 0x00 if their lengths are different.

    :param nonces: List of bytes, nonces to check
    :param minimal_hamming_distance: A stringified int, the minimum hamming distance between any two nonces; stringified
                                     for convenience of calling from within RobotFramework tests.
    :returns: Nothing, but will raise a ValueError if at least two nonces are not diverse enough; the checker stops at
              the first violation it finds.
    """
    minimal_hamming_distance = int(minimal_hamming_distance)

    for nonce1, nonce2 in combinations(nonces, 2):
        # Pad the shorter nonce with zeros, so they are of the same length
        max_length = max(len(nonce1), len(nonce2))
        nonce1 = nonce1.ljust(max_length, b"\x00")
        nonce2 = nonce2.ljust(max_length, b"\x00")

        hamming_distance = sum(bin(n1 ^ n2).count("1") for n1, n2 in zip(nonce1, nonce2))
        if hamming_distance < minimal_hamming_distance:
            report = (
                f"Nonces are not diverse enough! Hamming distance between nonces {nonce1!r} and {nonce2!r} is "
                f"{hamming_distance}, but should have been at least {minimal_hamming_distance}."
            )

            # Convert bytes to binary strings, as it is an easier representation for humans to look at
            nonce1_bin = " ".join([format(n, "08b") for n in nonce1])
            nonce2_bin = " ".join([format(n, "08b") for n in nonce2])
            report += f"\nNonce1: {nonce1_bin}\nNonce2: {nonce2_bin}"
            raise ValueError(report)


def nonces_must_be_unique(nonces: List[bytes]):
    """Check that a list of nonces are all unique.

    :param nonces: list of bytes, nonces to check
    :returns: nothing, but will raise a ValueError if the nonces are not unique
    """
    # uncomment this to provoke an error by duplicating a nonce
    # nonces.append(nonces[0])
    nonce_counts = Counter(nonces)
    repeated_nonces = [(nonce, count) for nonce, count in nonce_counts.items() if count > 1]

    if repeated_nonces:
        raise ValueError(f"Nonces are not unique! Repeated nonces with counts: {repeated_nonces}")


def log_asn1(pyasn1_obj: base.Asn1Type):
    """Log a pyasn1 object as a string for debugging purposes.

    For convenience, it will gracefully ignore objects that are not pyasn1, so that the function can be invoked from
    RobotFramework scenarios without having to check the type of the object first.
    """
    if isinstance(pyasn1_obj, base.Asn1Type):
        logging.info(pyasn1_obj.prettyPrint())
    else:
        logging.info("Cannot prettyPrint this, it is not a pyasn1 object")


def log_base64(data: Union[bytes, str]):
    """Log some data as a base64 encoded string, this is useful for binary payloads."""
    if isinstance(data, bytes):
        logging.info(b64encode(data))
    elif isinstance(data, str):
        logging.info(b64encode(data.encode("ascii")))


def manipulate_first_byte(data: bytes) -> bytes:
    """Manipulate a buffer to change its first byte to 0x00 (or to 0x01 if it was 0x00).

    This is useful if you want to deliberately break a cryptographic signature.

    :param data: bytes, buffer to modify
    :returns: bytes, modified buffer
    """
    if data[0] == 0:
        return b"\x01" + data[1:]
    return b"\x00" + data[1:]


def buffer_length_must_be_at_least(data: bytes, length: Strint) -> None:
    """Check whether the length of a byte buffer is at least `length` bytes.

    :param data: bytes, the buffer to examine
    :param length: stringified int, the minimum required length in bytes; it will come as a string
                   from RobotFramework, just as a matter of convenience of the caller.
    """
    if not len(data) >= int(length):
        raise ValueError(f"Buffer length {len(data)} < {length}, but should have been >={length} bytes!")


@keyword(name="Decode PEM String")
def decode_pem_string(data: Union[bytes, str]) -> bytes:
    """Decode a PEM-encoded string or byte sequence to its raw DER-encoded bytes.

    :param data: (str, bytes) the data to decode.
    :return: bytes The decoded DER-encoded bytes extracted from the PEM input
    """
    if isinstance(data, bytes):
        data = data.decode("ascii")

    raw = data.splitlines()
    filtered_lines = []
    # first do some cosmetic filtering
    for line in raw:
        if line.startswith("#"):  # remove comments
            continue
        if line.strip() == "":  # remove blank lines
            continue

        filtered_lines.append(line)

    if "-----BEGIN" in filtered_lines[0]:
        result = "".join(filtered_lines[1:-1])
    else:
        result = "".join(filtered_lines)

    # note that b64decode doesn't care about \n in the string to be decoded, so we keep them to potentially improve
    # readability when debugging.
    return b64decode(result)


@keyword("Load And Decode PEM File")
def load_and_decode_pem_file(path: str):
    """Load a base64-encoded PEM file, with or without a header, ignore comments, and return the decoded data.

    This is an augmented version of the PEM format, which allows one to add comments to the file, by starting the
    line with a # character. This is purely a convenience for the user, and is not part of the standard.

    :param path: str, path to the file you want to load
    :returns: bytes, the data loaded from the file.
    """
    # normally it should always have a header/trailer (aka "armour"), but we'll be tolerant to that.

    filtered_lines = []
    with open(path, "r", encoding="ascii") as f:
        raw = f.readlines()
        # first do some cosmetic filtering
        for line in raw:
            if line.startswith("#"):  # remove comments
                continue
            if line.strip() == "":  # remove blank lines
                continue

            filtered_lines.append(line)

    if "-----BEGIN" in filtered_lines[0]:
        result = "".join(filtered_lines[1:-1])
    else:
        result = "".join(filtered_lines)

    # note that b64decode doesn't care about \n in the string to be decoded, so we keep them to potentially improve
    # readability when debugging.
    return b64decode(result)


def strip_armour(raw: bytes) -> bytes:
    """Remove PEM armour, like -----BEGIN CERTIFICATE REQUEST----- and -----END CERTIFICATE REQUEST-----.

    :param raw: bytes, input structure
    :returns: bytes unarmoured data
    """
    result = raw.decode("ascii")
    result = re.sub("-----BEGIN .*?-----", "", result)
    result = re.sub("-----END .*?-----", "", result)
    result = result.replace("\n", "")
    return bytes(result, "ascii")


def log_data_type(data: Any) -> None:
    """Log the python datatype of the data parsed.

    :param data: Any
    :return:
    """
    logging.info(type(data))


if __name__ == "__main__":
    print(load_and_decode_pem_file("../data/1.3.6.1.4.1.2.267.7.4.4-dilithium2/csr.pem"))


def pem_to_der(pem_data: Union[str, bytes]) -> bytes:
    """Convert PEM-encoded data to DER-encoded format.

    :param pem_data: The PEM-encoded as a string or bytes.
    :return: The DER-encoded data as bytes.
    """
    if isinstance(pem_data, bytes):
        pem_data = pem_data.decode("utf-8")

    # Split the PEM string into lines
    lines = pem_data.strip().splitlines()

    # Filter out the header and footer lines
    pem_body = "".join(line for line in lines if not line.startswith("-----"))

    # Decode the base64 encoded content to DER format
    der_data = base64.b64decode(pem_body)

    return der_data


@not_keyword
def filter_options(  # type: ignore
    options: List[str], include: Optional[str] = None, exclude: Optional[str] = None
) -> List[str]:
    """Return the option to exclude with the provided string representations.

    :param options: All possible options to parse.
    :param include: A comma-separated string of options that should be included.
    (other options will be automatically excluded)
    :param exclude: A comma-separated string of options that should be excluded.
    :return: the options to exclude.
    """
    if exclude is None and include is None:
        return []
    if include is None:
        return exclude.strip(" ").split(",")  # type: ignore

    include_fields = include.strip(" ").split(",")
    exclude: List[str] = []  # type: ignore
    for option in options:
        if option not in include_fields:
            exclude.append(option)

    return exclude


def log_certificates(  # noqa D417 undocumented-param
    certs: List[rfc9480.CMPCertificate], msg_suffix: Optional[str] = None
):
    """Log a list of certificates in `pyasn1` format for better readability and user experience.

    Converts the provided certificates (either `pyasn1` or `cryptography` certificates)
    to their ASN.1 representation and logs them in a human-readable format using `prettyPrint()`.

    Arguments:
    ---------
        - `certs`: A list of certificates to be logged. Each certificate can be either
          a `pyasn1` or `cryptography` certificate object.
        - `msg_suffix`: A custom message suffix to append to the log. Defaults to `None`.

    Examples:
    --------
    | Log Certificates | ${cert_list} |
    | Log Certificates | ${cert_list} | msg_suffix="Certificate Details: " |

    """
    if msg_suffix is None:
        msg_suffix = "%s"
    else:
        msg_suffix += "%s"

    asn1certs = univ.SequenceOf()
    asn1certs.extend(certs)
    logging.info(msg_suffix, asn1certs.prettyPrint())


def write_certs_to_dir(  # noqa D417 undocumented-param
    cert_chain: List[rfc9480.CMPCertificate], name_prefix: Optional[str] = None, directory="data/cert_logs"
) -> None:
    """Write a list of certificates (cert chain) to a specified directory as PEM files.

    Writes each certificate from a certificate chain to a directory in PEM format. The certificates
    will be named according to either a provided `name_prefix` followed by an index or the subject name of the
    certificate.

    Arguments:
    ---------
        - `cert_chain`: A list of certificates to be written to files.
        - `name_prefix`: A prefix for naming each certificate file, followed by the certificate's index
                                         in the chain. If not provided, the subject name of each certificate will be
                                         used as the filename.
        - `directory`: The directory where the certificate files will be written. Defaults to "cert_logs".

    Examples:
    --------
    | Write Certs To File | cert_chain=${CERT_CHAIN} | name_prefix="cert_num" | directory="/path/to/logs" |
    | Write Certs To File | cert_chain=${CERT_CHAIN} | name_prefix="cert_num" |

    """
    os.makedirs(directory, exist_ok=True)
    for i, cert in enumerate(cert_chain):
        if name_prefix is None:
            subject = get_openssl_name_notation(cert["tbsCertificate"]["subject"])  # type: ignore
            if subject is None:
                raise ValueError("subject of Certificate can not be None!")
            subject = subject.strip()  # type: ignore
        else:
            subject = name_prefix + f"_{i}"

        tmp_path = os.path.join(directory, subject + ".pem")
        write_cmp_certificate_to_pem(path=tmp_path, cert=cert)


@not_keyword
def pyasn1_cert_to_pem(cert: rfc9480.CMPCertificate) -> str:
    """Convert a `pyasn1` rfc9480.CMPCertificate into a PEM string.

    :param cert: The certificate to decode/convert.
    :return: The PEM string.
    """
    der_cert = encoder.encode(cert)
    b64_encoded = base64.b64encode(der_cert).decode("utf-8")
    b64_encoded = "\n".join(textwrap.wrap(b64_encoded, width=64))
    pem_cert = "-----BEGIN CERTIFICATE-----\n" + b64_encoded + "\n-----END CERTIFICATE-----\n"
    return pem_cert


@not_keyword
def pyasn1_csr_to_pem(csr: rfc6402.CertificationRequest) -> bytes:
    """Convert a `pyasn1` rfc9480.CMPCertificate into a PEM string.

    :param csr: The certificate to decode/convert.
    :return: The PEM string as bytes.
    """
    der_cert = encoder.encode(csr)
    b64_encoded = base64.b64encode(der_cert).decode("utf-8")
    b64_encoded = "\n".join(textwrap.wrap(b64_encoded, width=64))
    pem_cert = "-----BEGIN CERTIFICATE REQUEST-----\n" + b64_encoded + "\n-----END CERTIFICATE REQUEST-----\n"
    return pem_cert.encode("utf-8")


def write_cmp_certificate_to_pem(cert: rfc9480.CMPCertificate, path: str) -> None:
    """Write a certificate in PEM format to a specified file path.

    :param cert: The certificate object to be written.
    :param path: Path to the file where the PEM certificate will be written
    :return:
    """
    with open(path, "w", encoding="utf-8") as pem_file:
        pem_file.write(pyasn1_cert_to_pem(cert))


def load_certificate_chain(filepath: str) -> List[rfc9480.CMPCertificate]:
    """Load and decode all certificates from a PEM-encoded certificate chain.

    :param filepath: path of the file containing the certificate chain.
    :return: List of `rfc9480.CMPCertificate` objects.
    """
    certificates = []
    certificate = []
    inside_certificate = False
    pem_certificates = []

    with open(filepath, "r", encoding="utf-8") as file:
        for line in file:
            if line.startswith("#"):  # remove comments
                continue
            if line.strip() == "":  # remove blank lines
                continue
            if "-----BEGIN CERTIFICATE-----" in line:
                inside_certificate = True
                certificate = []
            elif "-----END CERTIFICATE-----" in line:
                inside_certificate = False
                pem_certificates.append("".join(certificate))
            elif inside_certificate:
                certificate.append(line)

    for pem_cert in pem_certificates:
        der_bytes = b64decode("".join(pem_cert))
        cert, _ = decoder.decode(der_bytes, asn1Spec=rfc9480.CMPCertificate())
        certificates.append(cert)

    return certificates


# moved here because of cyclic-import
@not_keyword
def get_openssl_name_notation(
    name: rfc9480.Name,
    oids: Optional[Iterable[univ.ObjectIdentifier]] = None,
    return_dict=False,
) -> Union[str, None, dict]:
    """Extract a common name from a `pyasn1` Name object using specific OIDs.

    :param name: The `pyasn1` Name object. Expect an object, which was sent over the wire (decoded!).
    :param oids: List of ObjectIdentifier.
    :param return_dict: Whether to return the extracted name as python dictionary or string.
    :return: A name in OpenSSL notation, e.g., "C=DE,ST=Bavaria,L= Munich,CN=Joe Mustermann" or a dict or
    None if the oids where not inside.
    """
    out_name = None
    dict_data = {}

    if oids is None:
        oids = PYASN1_CM_NAME_2_OIDS.keys()

    for rdn in name["rdnSequence"]:
        attribute: rfc2986.AttributeTypeAndValue
        for attribute in rdn:
            if attribute["type"] in oids:
                # need to remove asn1 type value.
                dict_data[PYASN1_CM_NAME_2_OIDS.get(attribute["type"])] = (
                    decoder.decode(attribute["value"])[0]
                ).prettyPrint()
                if out_name is None:
                    out_name = (
                        f"{PYASN1_CM_NAME_2_OIDS.get(attribute['type'])}="
                        + (decoder.decode(attribute["value"])[0]).prettyPrint()
                    )
                else:
                    out_name += (
                        f",{PYASN1_CM_NAME_2_OIDS.get(attribute['type'])}="
                        + (decoder.decode(attribute["value"])[0]).prettyPrint()
                    )

    if return_dict:
        return dict_data

    return out_name


@not_keyword
def load_crl_from_file(path: str) -> rfc5280.CertificateList:
    """Load a CRL from a filepath.

    :param path: The filepath of the file to load the CRL.
    :return: The loaded `rfc5280.CertificateList` structure.
    """
    crl_der = load_and_decode_pem_file(path)
    crl, _ = decoder.decode(crl_der, asn1Spec=rfc5280.CertificateList())
    return crl


def may_load_cert_and_key(  # noqa D417 undocumented-param
    cert_path: Optional[str] = None,
    key_path: Optional[str] = None,
    key_password: Union[None, str] = "11111",
    key_type: Optional[str] = None,
) -> Union[Tuple[None, None], Tuple[rfc9480.CMPCertificate, PrivateKey]]:
    """Load a certificate and private key from specified file paths.

    Attempts to load a certificate and its corresponding private key from
    provided file paths. Used to verify if a certificate is provided to start
    the test suite if, MAC-based-protection is disabled.

    Arguments:
    ---------
        - `cert_path`: Optional string specifying the path to the certificate file.
        - `key_path`: Optional string specifying the path to the private key file.
        - `key_password`: A string representing the password for the private key file.
                          Defaults to `"11111"`.
        - `key_type`: Optional string specifying the type of private key (e.g., "RSA" or "ECDSA").
                      Defaults to `None`.

    Returns:
    -------
        - A tuple containing the loaded certificate and the corresponding private key

    Raises:
    ------
        - `ValueError`: If only one of `cert_path` or `key_path` is provided, or if the private key
                        does not match the public key in the certificate.

    Examples:
    --------
    | ${cert} ${key}= | May Load Cert and Key | cert_path=/path/to/cert.pem | key_path=/path/to/key.pem |
    | ${cert} ${key}= | May Load Cert and Key | cert_path=None | key_path=None |

    """
    if cert_path is None and key_path is None:
        logging.info("Starts without loading a initial certificate and private key.")
        return None, None

    if not cert_path or not key_path:
        raise ValueError("Both paths needs to be provided!")

    der_cert = load_and_decode_pem_file(cert_path)
    cert = certutils.parse_certificate(der_cert)

    key = keyutils.load_private_key_from_file(filepath=key_path, password=key_password, key_type=key_type)

    cert_pub_key = certutils.load_public_key_from_cert(cert)  # type: ignore
    if key.public_key() != cert_pub_key:
        raise ValueError("The private key and the public key inside the certificate are not a Pair!")

    return cert, key


def is_certificate_and_key_set(  # noqa D417 undocumented-param
    cert: Optional[rfc9480.CMPCertificate] = None, key: Optional[PrivateKey] = None
) -> bool:
    """Check if a certificate and its corresponding private key are valid and set.

    Is needed because the Robot Framework cannot check if a `pyasn1` certificate is None.

    Arguments:
    ---------
        - `cert`: The certificate to validate. Default is `None`.
        - `key`: The private key to validate against the certificate. Default is `None`.

    Returns:
    -------
        - `True` if both the certificate and key are set and match, `False` if both are None.

    Raises:
    ------
        - `ValueError`: If the provided private key does not match the public key in the certificate.

    Examples:
    --------
    | ${is_valid}= | Is Certificate And Key Set | cert=${certificate} | key=${private_key} |
    | ${is_valid}= | Is Certificate And Key Set | cert=None | key=None |

    """
    if cert is None and key is None:
        return False

    cert_pub_key = certutils.load_public_key_from_cert(cert)  # type: ignore
    if key.public_key() != cert_pub_key:
        raise ValueError("The private key and the public key inside the certificate are not a pair!")

    return True


def check_if_private_key_in_list(  # noqa D417 undocumented-param
    keys: List[PrivateKey], new_key: PrivateKey
) -> bool:
    """Check if a private key is already present in a list of private keys.

    Since private keys cannot be directly compared, this function compares the public keys
    associated with each private key to determine if the `new_key` already exists in the `keys` list.

    Arguments:
    ---------
        - `keys`: A list of `PrivateKey` objects to check against.
        - `new_key`: The `PrivateKey` to check for presence in the list, based on its associated public key.

    Returns:
    -------
        - `True` if the public key of `new_key` matches any public key in the `keys` list. `False` otherwise.

    Examples:
    --------
    | ${is_duplicate}= | Check If Private Key In List | keys=${private_key_list} | new_key=${new_private_key} |
    | ${is_duplicate}= | Check If Private Key In List | keys=${existing_keys} | new_key=${another_private_key} |

    """
    for key in keys:
        if key.public_key() == new_key.public_key():
            return True

    return False


def log_cert_chain_subject_and_issuer(certs: Iterable[rfc9480.CMPCertificate]):  # noqa D417 undocumented-param
    """Log the subject and the issuer of a certificate, for everyone provided.

    Arguments:
    ---------
        - `certs`: A list of certificates.

    Examples:
    --------
    | Log Cert Chain Subject And Issuer | ${cert_chain} |


    """
    for cert in certs:
        logging.info("%s", _get_subject_and_issuer(cert))


def _get_subject_and_issuer(cert: rfc9480.CMPCertificate) -> str:
    """Return a concatenated string fo the issuer and subject of a certificate.

    :param cert: The certificate to extract the values from.
    :return: "issuer=%s, subject=%s"
    """
    issuer_name = get_openssl_name_notation(cert["tbsCertificate"]["issuer"])
    subject_name = get_openssl_name_notation(cert["tbsCertificate"]["subject"])
    return f"subject={subject_name}, issuer={issuer_name}"


@not_keyword
def ensure_list(data: Optional[Union[List[Any], Any]]) -> list:
    """Ensure that a parsed object is a list.

    If `None` is provided, an empty list will be returned.

    :param data: The data to convert to a list.
    :return: A list.
    """
    if data is None:
        return []
    if isinstance(data, list):
        return data

    return [data]


def manipulate_composite_sig(sig: bytes) -> bytes:
    """Manipulate the first signature of a CompositeSignature.

    :param sig: The DER-encoded signature.
    :return: The modified signature.
    """
    obj, _ = decoder.decode(sig, CompositeSignatureValue())

    sig1 = obj[0].asOctets()
    sig2 = obj[1].asOctets()

    sig1 = manipulate_first_byte(sig1)

    sig1 = univ.BitString.fromOctetString(sig1)
    sig2 = univ.BitString.fromOctetString(sig2)

    out = CompositeSignatureValue()

    out.append(sig1)
    out.append(sig2)
    return encoder.encode(out)
