from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, ec, ed25519, ed448, dsa, x25519, x448
from robot.api.deco import not_keyword

from oid_mapping import hash_name_to_instance
from typingutils import PublicKeySig


def verify_signature(public_key: PublicKeySig, signature: bytes, data: bytes, hash_alg: str = None) -> None:
    """Verify a digital signature using the provided public key and data.
    Supports: (ECDSA, ED448, ED25519, RSA, DSA).

    :param public_key: A `cryptography` public key object (e.g., Elliptic Curve, Ed25519, Ed448, DSA)
                       used to verify the signature.
    :param signature: The digital signature to be verified, provided as a byte sequence.
    :param data: The original data that was signed, provided as a byte sequence.
    :param hash_alg: Optional string representing the name of the hash algorithm to be used for verification
                     (e.g., "sha256"). If not specified, the default algorithm for the given key type is used.

    :raises
        InvalidSignature: If an unsupported key type is provided.
        ValueError: If the Signature is Invalid.
    """
    if hash_alg is not None and not isinstance(hash_alg, hashes.HashAlgorithm):
        hash_alg = hash_name_to_instance(hash_alg)
    # isinstance(ed448.Ed448PrivateKey.generate(), EllipticCurvePrivateKey) → False
    # so can check in this Order.
    if isinstance(public_key, ec.EllipticCurvePublicKey):
        public_key.verify(signature, data, ec.ECDSA(hash_alg))
    elif isinstance(public_key, ed25519.Ed25519PublicKey):
        public_key.verify(signature, data)
    elif isinstance(public_key, ed448.Ed448PublicKey):
        public_key.verify(signature, data)
    elif isinstance(public_key, dsa.DSAPublicKey):
        public_key.verify(signature, data, hash_alg)
    elif isinstance(public_key, (x25519.X25519PublicKey, x448.X448PublicKey)):
        raise ValueError(
            f"Key type '{type(public_key).__name__}' is not used for signing or verifying signatures. It is used for key exchange."
        )
    else:
        raise ValueError(f"Unsupported public key type: {type(public_key).__name__}.")


@not_keyword
def verify_cert_signature(certificate: x509.Certificate):
    """Verify the digital signature of an X.509 certificate using the provided or extracted public key.

    :param certificate:
        The certificate to verify, represented in a type that can be cast to an X.509 certificate object.
        It should be in a DER-encoded form compatible with the `x509.Certificate` type.

    :raises InvalidSignature:
        If the certificate's signature is not valid when verified against the provided or extracted public key.
    """


    verify_signature(public_key=certificate.public_key(),
                     signature=certificate.signature,
                     data=certificate.tbs_certificate_bytes,
                     hash_alg=certificate.signature_hash_algorithm)


@not_keyword
def verify_csr_signature(csr: x509.CertificateSigningRequest):
    """Verify the digital signature of an X.509 CSR using the provided or extracted public key.

    :param csr:
        The Certificate Signing Request to verify, represented in a type that can be cast to an X.509 CSR object.
        It should be in a DER-encoded form compatible with the `x509.Certificate` type.

    :raises InvalidSignature:
        If the csr's signature is not valid when verified against the provided or extracted public key.
    """

    verify_signature(public_key=csr.public_key(),
                     signature=csr.signature,
                     data=csr.tbs_certrequest_bytes,
                     hash_alg=csr.signature_hash_algorithm)
