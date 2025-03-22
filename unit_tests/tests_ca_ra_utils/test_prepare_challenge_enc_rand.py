# SPDX-FileCopyrightText: Copyright 2024 Siemens AG
#
# SPDX-License-Identifier: Apache-2.0

import unittest

from pyasn1.codec.der import decoder, encoder
from resources.asn1_structures import ChallengeASN1
from resources.ca_ra_utils import prepare_challenge_enc_rand
from resources.keyutils import load_private_key_from_file


class TestPrepareChallengeEncRand(unittest.TestCase):


    @classmethod
    def setUpClass(cls):
        cls.rsa_key = load_private_key_from_file("./data/keys/private-key-rsa.pem", password=None)
        cls.mlkem_key = load_private_key_from_file("./data/keys/private-key-ml-kem-768.pem")

    def test_prepare_with_rsa(self):
        """
        GIVEN a valid RSA private key.
        WHEN preparing a challenge with RSA.
        THEN the challenge is valid.
        """
        challenge = prepare_challenge_enc_rand(public_key=self.rsa_key.public_key(),
        sender="CN=Hans the Tester")

        der_data = encoder.encode(challenge)
        decoded_obj, rest = decoder.decode(der_data, asn1Spec=ChallengeASN1())
        self.assertEqual(rest, b"")

    def test_prepare_with_kem(self):
        """
        GIVEN a valid KEM public key.
        WHEN preparing a challenge with KEM `kari`.
        THEN the challenge is valid.
        """
        challenge = prepare_challenge_enc_rand(public_key=self.mlkem_key.public_key(),
        sender="CN=Hans the Tester")
        der_data = encoder.encode(challenge)
        decoded_obj, rest = decoder.decode(der_data, asn1Spec=ChallengeASN1())
        self.assertEqual(rest, b"")


    def test_prepare_with_xwing(self):
        """
        GIVEN a valid XWing private key and a public key.
        WHEN preparing a challenge with XWing.
        THEN the challenge is valid.
        """
        xwing_key = load_private_key_from_file("./data/keys/private-key-xwing.pem")
        xwing_key_other = load_private_key_from_file("./data/keys/private-key-xwing-other.pem")
        challenge = prepare_challenge_enc_rand(public_key=xwing_key.public_key(),
        sender="CN=Hans the Tester", hybrid_kem_key=xwing_key_other)
        der_data = encoder.encode(challenge)
        decoded_obj, rest = decoder.decode(der_data, asn1Spec=ChallengeASN1())
        self.assertEqual(rest, b"")
