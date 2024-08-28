from pyasn1.type.univ import BitString
from pyasn1_alt_modules import rfc9480
from pyasn1_alt_modules.rfc4210 import PKIMessage

import utils
from cmputils import parse_pki_message


def generate_pki_status_info(bit_stream: str | None = None) -> rfc9480.PKIStatusInfo:
    """
    Generates a PKIStatusInfo object with a predefined status and failInfo.

    :return: A PKIStatusInfo object populated with a status and failInfo.
    :rtype: rfc9480.PKIStatusInfo
    """



    # Access the pkiStatusInfo within the PKIMessage
    status_info = rfc9480.PKIStatusInfo()

    # Set the status (e.g., rejection which might be represented by 2 in your schema)
    status_info.setComponentByName('status', 2)


    if bit_stream is None:
        fail_info = BitString()
    else:
        # pass
        # Set the failInfo (BitString)
        fail_info = BitString(f"'{bit_stream}'B")  # Example BitString value


    status_info.setComponentByName('failInfo', fail_info)

    return status_info


def generate_pki_message_with_failure_info(bit_stream: str | None = None) -> PKIMessage:


    pki_msg: rfc9480.PKIMessage = parse_pki_message(utils.load_and_decode_pem_file(
        "data/example-p10cr-rufus.pem"
    ))

    value = generate_pki_status_info(bit_stream)
    pki_msg["body"]["error"].setComponentByName('pKIStatusInfo', value)
    return pki_msg



def generate_pki_message_without_failure_info() -> rfc9480.PKIMessage:
    """
    Generates a PKIMessage object with a predefined status but without failInfo.

    :return: A PKIMessage object populated with a status but without failInfo.
    :rtype: rfc9480.PKIMessage
    """

    pki_msg: rfc9480.PKIMessage = parse_pki_message(utils.load_and_decode_pem_file(pem_file_path))

    value = generate_pki_status_info(None)
    pki_msg["body"]["error"].setComponentByName('pKIStatusInfo', value)
    return pki_msg




