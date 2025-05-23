# SPDX-FileCopyrightText: Copyright 2024 Siemens AG
#
# SPDX-License-Identifier: Apache-2.0
#
# ruff: noqa: D104 Missing docstring in public package
# ruff: noqa: D102 Missing docstring in public method
# ruff: noqa: D401 First line of docstring should be in imperative mood
# ruff: noqa: E711 Comparison to `None` should be `cond is not None`

"""Contains the ML-DSA implementation based on FIPS 204."""

#   fips204.py
#   2024-08-16  Markku-Juhani O. Saarinen <mjos@iki.fi> See LICENSE.
#   === FIPS 204 implementation https://doi.org/10.6028/NIST.FIPS.204
#   ML-DSA / Module-Lattice-Based Digital Signature Standard
#   test_mldsa is only used by the unit test in the end
# from test_mldsa import test_mldsa
#   hash functions

from typing import Optional, Tuple

# from Crypto.Hash import SHA256, SHA512, SHAKE128
from cryptography.hazmat.primitives import hashes

from pq_logic.fips._fips_utils import XOFHash, _compute_shake, _compute_hash

ML_DSA_Q = 8380417
ML_DSA_N = 256

#   Appendix B - Zetas Array

ML_DSA_ZETAS = [
    0,
    4808194,
    3765607,
    3761513,
    5178923,
    5496691,
    5234739,
    5178987,
    7778734,
    3542485,
    2682288,
    2129892,
    3764867,
    7375178,
    557458,
    7159240,
    5010068,
    4317364,
    2663378,
    6705802,
    4855975,
    7946292,
    676590,
    7044481,
    5152541,
    1714295,
    2453983,
    1460718,
    7737789,
    4795319,
    2815639,
    2283733,
    3602218,
    3182878,
    2740543,
    4793971,
    5269599,
    2101410,
    3704823,
    1159875,
    394148,
    928749,
    1095468,
    4874037,
    2071829,
    4361428,
    3241972,
    2156050,
    3415069,
    1759347,
    7562881,
    4805951,
    3756790,
    6444618,
    6663429,
    4430364,
    5483103,
    3192354,
    556856,
    3870317,
    2917338,
    1853806,
    3345963,
    1858416,
    3073009,
    1277625,
    5744944,
    3852015,
    4183372,
    5157610,
    5258977,
    8106357,
    2508980,
    2028118,
    1937570,
    4564692,
    2811291,
    5396636,
    7270901,
    4158088,
    1528066,
    482649,
    1148858,
    5418153,
    7814814,
    169688,
    2462444,
    5046034,
    4213992,
    4892034,
    1987814,
    5183169,
    1736313,
    235407,
    5130263,
    3258457,
    5801164,
    1787943,
    5989328,
    6125690,
    3482206,
    4197502,
    7080401,
    6018354,
    7062739,
    2461387,
    3035980,
    621164,
    3901472,
    7153756,
    2925816,
    3374250,
    1356448,
    5604662,
    2683270,
    5601629,
    4912752,
    2312838,
    7727142,
    7921254,
    348812,
    8052569,
    1011223,
    6026202,
    4561790,
    6458164,
    6143691,
    1744507,
    1753,
    6444997,
    5720892,
    6924527,
    2660408,
    6600190,
    8321269,
    2772600,
    1182243,
    87208,
    636927,
    4415111,
    4423672,
    6084020,
    5095502,
    4663471,
    8352605,
    822541,
    1009365,
    5926272,
    6400920,
    1596822,
    4423473,
    4620952,
    6695264,
    4969849,
    2678278,
    4611469,
    4829411,
    635956,
    8129971,
    5925040,
    4234153,
    6607829,
    2192938,
    6653329,
    2387513,
    4768667,
    8111961,
    5199961,
    3747250,
    2296099,
    1239911,
    4541938,
    3195676,
    2642980,
    1254190,
    8368000,
    2998219,
    141835,
    8291116,
    2513018,
    7025525,
    613238,
    7070156,
    6161950,
    7921677,
    6458423,
    4040196,
    4908348,
    2039144,
    6500539,
    7561656,
    6201452,
    6757063,
    2105286,
    6006015,
    6346610,
    586241,
    7200804,
    527981,
    5637006,
    6903432,
    1994046,
    2491325,
    6987258,
    507927,
    7192532,
    7655613,
    6545891,
    5346675,
    8041997,
    2647994,
    3009748,
    5767564,
    4148469,
    749577,
    4357667,
    3980599,
    2569011,
    6764887,
    1723229,
    1665318,
    2028038,
    1163598,
    5011144,
    3994671,
    8368538,
    7009900,
    3020393,
    3363542,
    214880,
    545376,
    7609976,
    3105558,
    7277073,
    508145,
    7826699,
    860144,
    3430436,
    140244,
    6866265,
    6195333,
    3123762,
    2358373,
    6187330,
    5365997,
    6663603,
    2926054,
    7987710,
    8077412,
    3531229,
    4405932,
    4606686,
    1900052,
    7598542,
    1054478,
    7648983,
]

#   zetas = [ (1753 ** self.bitrev8(i)) % ML_DSA_Q for i in range(256) ]

#   Sect 4, Table 1. ML-DSA parameter sets

#   (d, tau, lam, gam1, gam2, k, ell, eta, beta, omega)
ML_DSA_PARAM = {
    "ml-dsa-44": (13, 39, 128, 2**17, (ML_DSA_Q - 1) // 88, 4, 4, 2, 78, 80),
    "ml-dsa-65": (13, 49, 192, 2**19, (ML_DSA_Q - 1) // 32, 6, 5, 4, 196, 55),
    "ml-dsa-87": (13, 60, 256, 2**19, (ML_DSA_Q - 1) // 32, 8, 7, 2, 120, 75),
}


class ML_DSA:
    """The ML-DSA class."""

    def __init__(self, param: str = "ml-dsa-65"):
        """Initialize the class with parameters."""
        param = param.lower()
        if param not in ML_DSA_PARAM:
            raise ValueError(
                f"The parameter set is not supported.: {param}.Supported parameter sets are: {ML_DSA_PARAM.keys()}"
            )
        self.q = ML_DSA_Q
        self.n = ML_DSA_N
        (self.d, self.tau, self.lam, self.gam1, self.gam2, self.k, self.ell, self.eta, self.beta, self.omega) = (
            ML_DSA_PARAM[param]
        )

    #   3.7 Use of Symmetric Cryptography
    def h(self, s, length):
        xof = hashes.SHAKE256(length)
        hasher = hashes.Hash(xof)
        hasher.update(s)
        return hasher.finalize()

    #   Algorithm 2, ML-DSA.Sign(sk, M, ctx)
    #   XXX: Not covered by test vectors.

    def sign(self, sk: bytes, m: bytes, ctx: bytes, rnd_in: Optional[bytes] = None, param: Optional[str] = None):
        """Sign the message.

        :param sk: The secret key.
        :param m: The message to sign.
        :param ctx: The context relevant to the signature.
        :param rnd_in: The random value. Defaults to `os.urandom(32)`.
        :param param: The name of the ML-DSA version in lowercase. Defaults to `None`.
        :return:
        """
        if param is not None:
            self.__init__(param)
        if len(ctx) > 255:
            return None

        if rnd_in is None:
            rnd = b"\x00" * 32
        else:
            rnd = rnd_in

        mp = self.integer_to_bytes(0, 1) + self.integer_to_bytes(len(ctx), 1) + ctx + m
        sig = self.sign_internal(sk, mp, rnd)
        return sig

    #   Algorithm 3, ML-DSA.Verify(pk, M, sigma, ctx)
    #   XXX: Not covered by test vectors.

    def verify(self, pk: bytes, m: bytes, sig: bytes, ctx: bytes, param: Optional[str] = None):
        """Verify the signature.

        :param pk: The public key.
        :param m: The message to verify.
        :param sig: The signature to verify.
        :param ctx: The context relevant to the signature.
        :param param: Optional the name of the ML-DSA version in lowercase.
        (e.g., "ml-dsa-44", "ml-dsa-65", "ml-dsa-87")
        :return:
        """
        if param is not None:
            self.__init__(param)
        if len(ctx) > 255:
            raise ValueError("The length of the context is greater than 255.")

        mp = self.integer_to_bytes(0, 1) + self.integer_to_bytes(len(ctx), 1) + ctx + m
        return self.verify_internal(pk, mp, sig)

    #   Algorithm 4, HashML-DSA.Sign(sk, M, ctx, PH)
    #   XXX: Not covered by test vectors.

    def hash_ml_dsa_sign(self, sk, m, ctx, ph, rnd_in=None, param=None):
        if param is not None:
            self.__init__(param)
        if len(ctx) > 255:
            return None

        if rnd_in is None:
            rnd = b"\x00" * 32
        else:
            rnd = rnd_in

        if ph == "SHA-256":
            oid = bytes([0x06, 0x09, 0x60, 0x86, 0x48, 0x01, 0x65, 0x03, 0x04, 0x02, 0x01])
            #phm = SHA256.new(m).digest()
            phm = _compute_hash("sha256", m)
        elif ph == "SHA-512":
            oid = bytes([0x06, 0x09, 0x60, 0x86, 0x48, 0x01, 0x65, 0x03, 0x04, 0x02, 0x03])
            # phm = SHA512.new(m).digest()
            phm = _compute_hash("sha512", m)
        elif ph == "SHAKE128":
            oid = bytes([0x06, 0x09, 0x60, 0x86, 0x48, 0x01, 0x65, 0x03, 0x04, 0x02, 0x0B])
            # phm = SHAKE128.new(m).read(256 // 8)
            phm = _compute_shake("shake128", m, 256 // 8)
        else:
            return None

        mp = self.integer_to_bytes(1, 1) + self.integer_to_bytes(len(ctx), 1) + ctx + oid + phm
        sig = self.sign_internal(sk, mp, rnd)
        return sig

    #   Algorithm 5, HashML-DSA.Verify(pk, M, sig, ctx, PH)
    #   Note 2024-08-20: Not covered by test vectors.

    def hash_ml_dsa_verify(self, pk, m, sig, ctx, ph, param=None):
        if param is not None:
            self.__init__(param)
        if len(ctx) > 255:
            return None

        if ph == "SHA-256":
            oid = bytes([0x06, 0x09, 0x60, 0x86, 0x48, 0x01, 0x65, 0x03, 0x04, 0x02, 0x01])
            # phm = SHA256.new(m).digest()
            phm = _compute_hash("sha256", m)
        elif ph == "SHA-512":
            oid = bytes([0x06, 0x09, 0x60, 0x86, 0x48, 0x01, 0x65, 0x03, 0x04, 0x02, 0x03])
            # phm = SHA512.new(m).digest()
            phm = _compute_hash("sha512", m)
        elif ph == "SHAKE128":
            oid = bytes([0x06, 0x09, 0x60, 0x86, 0x48, 0x01, 0x65, 0x03, 0x04, 0x02, 0x0B])
            # phm = SHAKE128.new(m).read(256 // 8)
            phm = _compute_shake("shake128", m, 256 // 8)
        else:
            return False

        mp = self.integer_to_bytes(1, 1) + self.integer_to_bytes(len(ctx), 1) + ctx + oid + phm
        return self.verify_internal(pk, mp, sig)

    #   Algorithm 6, ML-DSA.KeyGen_internal(xi)

    def keygen_internal(self, xi: bytes, param: Optional[str] = None) -> Tuple[bytes, bytes]:
        """Generate the key pair.

        :param xi: The seed for the key pair.
        :param param: The name of the ML-DSA version in lowercase.
        (e.g., "ml-dsa-44", "ml-dsa-65", "ml-dsa-87")
        :return: The public key and the secret key.
        """
        if param is not None:
            self.__init__(param)
        # print('# keygen_internal()', param)
        # print('# seed:', xi.hex())
        se = self.h(xi + self.integer_to_bytes(self.k, 1) + self.integer_to_bytes(self.ell, 1), 128)
        rho = se[0:32]
        rhop = se[32:96]
        kk = se[96:128]
        # print('# rho:', rho.hex())
        # print('# rhoPrime:', rhop.hex())
        # print('# k:', kk.hex())

        ah = self.expand_a(rho)
        # print('# aHat:', ah)
        (s1, s2) = self.expand_s(rhop)
        # print('# s1:', s1)
        # print('# s2:', s2)

        s1h = [self.ntt(v) for v in s1]
        # print('# s1Hat:', s1h)

        t = self.matrix_vector_ntt(ah, s1h)
        # print('# aHat*s1Hat:', t)

        t = [self.add(self.ntt_inverse(t[i]), s2[i]) for i in range(self.k)]
        # print('# t:', t)

        (t1, t0) = self.power2round(t)
        # print('# t0:', t0)
        # print('# t1:', t1)

        pk = self.pk_encode(rho, t1)
        # print('# pk:', pk.hex())
        tr = self.h(pk, 64)
        # print('# tr:', tr.hex())

        sk = self.sk_encode(rho, kk, tr, s1, s2, t0)
        # print('# sk:', sk.hex())

        return pk, sk

    #   Algorithm 7, ML-DSA.Sign_internal(sk, M', rnd)

    def sign_internal(self, sk: bytes, mp: bytes, rnd: bytes, param: Optional[str] = None) -> bytes:
        """Internal function to sign the message.

        The prefix bytes and the extra information are set in the corresponding functions.

        :param sk: The secret key to sign the message.
        :param mp: The message to sign.
        :param rnd: A random value.
        :param param: The name of the ML-DSA version in lowercase.
        (e.g., "ml-dsa-44", "ml-dsa-65", "ml-dsa-87")
        :return: The signature.
        """
        if param is not None:
            self.__init__(param)

        (rho, kk, tr, s1, s2, t0) = self.sk_decode(sk)

        # print('# sign_internal()', param)
        # print('# rho:', rho.hex())
        # print('# tr:', tr.hex())
        # print('# rnd:', rnd.hex())

        s1h = [self.ntt(s1i) for s1i in s1]
        # print('# s1Hat:', s1h)
        s2h = [self.ntt(s2i) for s2i in s2]
        # print('# s2Hat:', s2h)
        t0h = [self.ntt(t0i) for t0i in t0]
        # print('# t0Hat:', t0h)

        ah = self.expand_a(rho)
        # print('# aHat:', ah)

        mu = self.h(tr + mp, 64)
        # print('# mu:', mu.hex())

        rhopp = self.h(kk + rnd + mu, 64)
        # print('# rhoPrime:', rhopp.hex())

        kappa = 0
        (z, h) = (None, None)
        while (z, h) == (None, None):
            y = self.expand_mask(rhopp, kappa)
            # print('# y:', y)

            yh = [self.ntt(yi) for yi in y]
            # print('# NTT(y):', yh)

            w = self.matrix_vector_ntt(ah, yh)
            # print('# aHat*NTT(y):', w)
            w = [self.ntt_inverse(wi) for wi in w]
            # print('# w:', w)

            w1 = self.high_bits(w)
            # print('# w1:', w1)

            w1t = self.w1_encode(w1)
            # print('# w1Encode:', w1t.hex())

            ct = self.h(mu + w1t, self.lam // 4)
            # print('# cTilde:', ct.hex())

            c = self.sample_in_ball(ct)
            # print('# c:', c)

            ch = self.ntt(c)
            # print('# cHat:', ch)

            cs1 = [self.ntt_inverse(self.mul_ntt(ch, s1i)) for s1i in s1h]
            # print('# cs1:', cs1)
            cs2 = [self.ntt_inverse(self.mul_ntt(ch, s2i)) for s2i in s2h]
            # print('# cs2:', cs2)

            z = [self.add(y[i], cs1[i]) for i in range(self.ell)]
            # print('# z:', z)

            r0 = [self.sub(w[i], cs2[i]) for i in range(self.k)]
            r0 = self.low_bits(r0)
            # print('# r0:', r0)

            z_norm = self.inf_norm(z)
            # print('# ||z||:', z_norm)

            r0_norm = self.inf_norm(r0)
            # print('# ||r0||:', r0_norm)

            if z_norm >= self.gam1 - self.beta or r0_norm >= self.gam2 - self.beta:
                # print('# norm check fail')
                (z, h) = (None, None)
            else:
                ct0 = [self.ntt_inverse(self.mul_ntt(ch, t0i)) for t0i in t0h]
                # print('# ct0:', ct0)
                ct0n = [self.neg(ct0i) for ct0i in ct0]
                # print('# -ct0:', ct0n)
                h_r = [self.add(self.sub(w[i], cs2[i]), ct0[i]) for i in range(self.k)]
                # print('# w - cs2 + ct0:', h_r)
                h = self.make_hint(ct0n, h_r)
                # print('# h', h)
                h_wt = self.weight(h)
                # print('# ||h||:', h_wt)

                ct0_norm = self.inf_norm(ct0)
                # print('# ||ct0||:', ct0_norm)
                if ct0_norm >= self.gam2 or h_wt > self.omega:
                    (z, h) = (None, None)
            kappa += self.ell

        z = [[self.modpm(x, self.q) for x in zi] for zi in z]
        sig = self.sig_encode(ct, z, h)
        # print('# sig:', sig.hex())

        return sig

    #   Algorithm 8, ML-DSA.Verify_internal(pk, M', sigma)

    def verify_internal(self, pk, mp, sig, param: Optional[str] = None) -> bool:
        """Internal function to verify a signature.

        Verify the already prepared signature, which includes the prefix bytes and the extra information.

        :param pk: The public key.
        :param mp: The message to verify.
        :param sig: The signature to verify.
        :param param: The name of the ML-DSA version in lowercase.
        (e.g., "ml-dsa-44", "ml-dsa-65", "ml-dsa-87")
        :return: True if the signature is valid, False otherwise.
        """
        if param is not None:
            self.__init__(param)

        (rho, t1) = self.pk_decode(pk)
        (ct, z, h) = self.sig_decode(sig)
        # print('# rho:', rho.hex())
        # print('# t1:', t1)
        # print('# cTilde:', ct.hex())
        # print('# z:', z)
        if h is None:
            return False

        ah = self.expand_a(rho)
        # print('# aHat:', ah)

        tr = self.h(pk, 64)
        # print('# tr:', tr.hex())

        mu = self.h(tr + mp, 64)
        # print('# mu:', mu.hex())

        c = self.sample_in_ball(ct)
        # print('# c:', c)

        zh = [self.ntt(zi) for zi in z]
        # print('# zHat:', zh)

        wp = self.matrix_vector_ntt(ah, zh)
        # print('# aHat*NTT(z):', wp)

        th = [self.ntt([x << self.d for x in t1i]) for t1i in t1]
        # print('# NTT(t1*2^d):', th)

        ch = self.ntt(c)
        # print('# NTT(c):', ch)

        th = [self.mul_ntt(ch, thi) for thi in th]
        # print('# NTT(c)*NTT(t1*2^d):', th)

        wp = [self.ntt_inverse(self.sub(wp[i], th[i])) for i in range(self.k)]
        # print('# wPrimeApprox:', wp)

        w1p = self.use_hint(h, wp)
        # print('# w1Prime;', w1p)

        ctp = self.h(mu + self.w1_encode(w1p), self.lam // 4)
        # print('# cTildePrime:', ctp.hex())

        z_norm = self.inf_norm(z)
        # print('# ||z||:', z_norm)

        return z_norm < self.gam1 - self.beta and ct == ctp

    #   Algorithm 9, IntegerToBits(x, alpha)

    def integer_to_bits(self, x, alpha):
        y = bytearray(alpha)
        for i in range(alpha):
            y[i] = x & 1
            x >>= 1
        return y

    #   Algorithm 10, BitsToInteger(y, alpha)

    def bits_to_integer(self, y, alpha):
        x = 0
        for i in range(1, alpha + 1):
            x = 2 * x + y[alpha - i]
        return x

    #   Algorithm 11, IntegerToBytes(x, alpha)

    def integer_to_bytes(self, x, alpha):
        y = bytearray(alpha)
        for i in range(alpha):
            y[i] = x & 0xFF
            x >>= 8
        return y

    #   Algorithm 12, BitsToBytes(y)

    def bits_to_bytes(self, y):
        alpha = len(y)
        z = bytearray(alpha // 8)
        for i in range(0, alpha, 8):
            x = 0
            for j in range(8):
                x += y[i + j] << j
            z[i // 8] = x
        return z

    #   Algorithm 13, BytesToBits(z)

    def bytes_to_bits(self, z):
        alpha = len(z)
        y = bytearray(8 * alpha)
        for i in range(alpha):
            x = z[i]
            for j in range(8):
                y[8 * i + j] = (x >> j) & 1
        return y

    #   Algorithm 14, CoeffFromThreeBytes(b0, b1, b2)

    def coeff_from_three_bytes(self, b0, b1, b2):
        if b2 > 127:
            b2 -= 128
        z = (b2 << 16) + (b1 << 8) + b0
        if z < self.q:
            return z
        else:
            return None

    #   Algorithm 15, CoeffFromHalfByte(b)

    def coeff_from_half_byte(self, b):
        if self.eta == 2 and b < 15:
            return 2 - (b % 5)
        elif self.eta == 4 and b < 9:
            return 4 - b
        else:
            return None

    #   Algorithm 16, SimpleBitPack(w, b)

    def simple_bit_pack(self, w, b):
        z = bytearray(0)
        bitlen_b = int(b).bit_length()
        for i in range(256):
            z += self.integer_to_bits(w[i], bitlen_b)
        return self.bits_to_bytes(z)

    #   Algorithm 17, BitPack(w, a, b)

    def bit_pack(self, w, a, b):
        c = int(a + b).bit_length()
        z = bytearray(0)
        for wi in w:
            z += self.integer_to_bits(b - wi, c)
        return self.bits_to_bytes(z)

    #   Algorithm 18, SimpleBitUnpack(v, b)

    def simple_bit_unpack(self, v, b):
        c = int(b).bit_length()
        z = self.bytes_to_bits(v)
        w = [None] * 256
        for i in range(256):
            w[i] = self.bits_to_integer(z[i * c : (i + 1) * c], c)
        return w

    #   Algorithm 19, BitUnpack(v, a, b)

    def bit_unpack(self, v, a, b):
        c = int(a + b).bit_length()
        z = self.bytes_to_bits(v)
        w = []
        for i in range(256):
            w += [b - self.bits_to_integer(z[i * c : (i + 1) * c], c)]
        return w

    #   Algorithm 20, HintBitPack(h)

    def hint_bit_pack(self, h):
        idx = 0
        y = bytearray(self.omega + self.k)
        for i in range(self.k):
            for j in range(256):
                if h[i][j] != 0:
                    y[idx] = j
                    idx += 1
            y[self.omega + i] = idx
        return y

    #   Algorithm 21, HintBitPack(h)

    def hint_bit_unpack(self, y):
        idx = 0
        h = [[0] * 256 for _ in range(self.k)]
        for i in range(self.k):
            if y[self.omega + i] < idx or y[self.omega + i] > self.omega:
                return None
            first = idx
            while idx < y[self.omega + i]:
                if idx > first:
                    if y[idx - 1] >= y[idx]:
                        return None
                h[i][y[idx]] = 1
                idx += 1
        for i in range(idx, self.omega):
            if y[i] != 0:
                return None
        return h

    #   Algorithm 22, pkEncode(rho, t1)

    def pk_encode(self, rho, t1):
        pk = rho
        b = 2 ** (int(self.q - 1).bit_length() - self.d) - 1
        for t1i in t1:
            pk += self.simple_bit_pack(t1i, b)
        return pk

    #   Algorithm 23, pkDecode(pk)

    def pk_decode(self, pk):
        rho = pk[0:32]
        bitlen_b = int(self.q - 1).bit_length() - self.d
        b = 2**bitlen_b - 1
        t1 = []
        for i in range(self.k):
            zi = pk[32 + 32 * bitlen_b * i : 32 + 32 * bitlen_b * (i + 1)]
            t1 += [self.simple_bit_unpack(zi, b)]
        return (rho, t1)

    #   Algorithm 24, skEncode(rho, K, tr, s1, s2, t0)

    def sk_encode(self, rho, kk, tr, s1, s2, t0):
        sk = rho + kk + tr
        for s1i in s1:
            sk += self.bit_pack(s1i, self.eta, self.eta)
        for s2i in s2:
            sk += self.bit_pack(s2i, self.eta, self.eta)
        for t0i in t0:
            sk += self.bit_pack(t0i, 2 ** (self.d - 1) - 1, 2 ** (self.d - 1))
        return sk

    #   Algorithm 25, skDecode(sk)

    def sk_decode(self, sk):
        rho = sk[0:32]
        kk = sk[32:64]
        tr = sk[64:128]
        pt = 128
        le = 32 * int(2 * self.eta).bit_length()
        s1 = []
        for i in range(self.ell):
            yi = sk[pt : pt + le]
            pt += le
            s1 += [self.bit_unpack(yi, self.eta, self.eta)]
        s2 = []
        for i in range(self.k):
            zi = sk[pt : pt + le]
            pt += le
            s2 += [self.bit_unpack(zi, self.eta, self.eta)]
        ld = 32 * self.d
        t0 = []
        for i in range(self.k):
            wi = sk[pt : pt + ld]
            pt += ld
            t0 += [self.bit_unpack(wi, 2 ** (self.d - 1) - 1, 2 ** (self.d - 1))]

        return (rho, kk, tr, s1, s2, t0)

    #   Algorithm 26, sigEncode(c~, z, h)

    def sig_encode(self, ct, z, h):
        sig = ct
        for i in range(self.ell):
            sig += self.bit_pack(z[i], self.gam1 - 1, self.gam1)
        sig += self.hint_bit_pack(h)
        return sig

    #   Algorithm 27, sigDecode(sig)

    def sig_decode(self, sig):
        bl = 32 * (1 + int(self.gam1 - 1).bit_length())
        cl = self.lam // 4
        ct = sig[0:cl]
        z = []
        for i in range(self.ell):
            xi = sig[cl + bl * i : cl + bl * (i + 1)]
            z += [self.bit_unpack(xi, self.gam1 - 1, self.gam1)]
        y = sig[cl + bl * self.ell : cl + bl * self.ell + self.omega + self.k]
        h = self.hint_bit_unpack(y)
        return (ct, z, h)

    #   Algorithm 28, w1Encode(w1)

    def w1_encode(self, w1):
        w1t = b""
        b = (self.q - 1) // (2 * self.gam2) - 1
        for w1i in w1:
            w1t += self.simple_bit_pack(w1i, b)
        return w1t

    #   Algorithm 29, SampleInBall(rho)

    def sample_in_ball(self, rho):
        c = [0] * 256
        # xof = SHAKE256.new(rho)
        xof = XOFHash("shake256")
        xof.update(rho)
        s = xof.read(8)
        h = self.bytes_to_bits(s)
        for i in range(256 - self.tau, 256):
            j = xof.read(1)[0]
            while j > i:
                j = xof.read(1)[0]
            c[i] = c[j]
            c[j] = (-1) ** h[i + self.tau - 256]
        return c

    #   Algorithm 30, RejNTTPoly(rho):

    def rej_ntt_poly(self, rho):
        j = 0
        # print('self.rej_ntt_poly', len(rho), rho.hex())
        # g = SHAKE128.new(rho)
        # The limit must not be lower than 298 rounds,
        # if a limit must be set.
        g = XOFHash("shake128")
        g.update(rho)
        a = [None] * 256
        while j < 256:
            s = g.read(3)
            a[j] = self.coeff_from_three_bytes(s[0], s[1], s[2])
            if a[j] is not None:
                j += 1
        return a

    #   Algorithm 31, RejBoundedPoly(rho)

    def rej_bounded_poly(self, rho):
        j = 0
        # h = SHAKE256.new(rho)
        h = XOFHash("shake256")
        h.update(rho)
        a = [None] * 256
        while j < 256:
            z = h.read(1)[0]
            z0 = self.coeff_from_half_byte(z % 16)
            z1 = self.coeff_from_half_byte(z // 16)
            if z0 != None:
                a[j] = z0
                j += 1
            if z1 != None and j < 256:
                a[j] = z1
                j += 1
        return a

    #   Algorithm 32, ExpandA(rho)

    def expand_a(self, rho):
        a = [[None] * self.ell for _ in range(self.k)]
        for r in range(self.k):
            for s in range(self.ell):
                rhop = rho + self.integer_to_bytes(s, 1) + self.integer_to_bytes(r, 1)
                a[r][s] = self.rej_ntt_poly(rhop)
        return a

    #   Algorithm 33, ExpandS(rho)

    def expand_s(self, rho):
        s1 = []
        for r in range(self.ell):
            s1 += [self.rej_bounded_poly(rho + self.integer_to_bytes(r, 2))]
        s2 = []
        for r in range(self.k):
            s2 += [self.rej_bounded_poly(rho + self.integer_to_bytes(r + self.ell, 2))]
        return (s1, s2)

    #   Algorithm 34, ExpandMask(rho, mu)

    def expand_mask(self, rho, mu):
        c = 1 + int(self.gam1 - 1).bit_length()
        y = []
        for r in range(self.ell):
            rhop = rho + self.integer_to_bytes(mu + r, 2)
            v = self.h(rhop, 32 * c)
            y += [self.bit_unpack(v, self.gam1 - 1, self.gam1)]
        return y

    """2.3 Mathematical Symbols:
    If alpha is a positive integer and m in Z or m in Z_alpha, then
    m mod^{+-} alpha denotes the unique element m' in Z in the
    range -ceil(alpha/2) < m' <= floor(alpha/2) such that m and m' are
    congruent modulo alpha.

    NOTE: This is *not* two's complement sign extension as it includes
    +alpha/2 and excludes -alpha/2. Hence the negations here.
    """

    def modpm(self, m, alpha):
        return -((alpha // 2 - m) % alpha) + (alpha // 2)

    def inf_norm(self, x):
        if isinstance(x, list):
            y = 0
            for xi in x:
                y = max(y, self.inf_norm(xi))
            return y
        else:
            return abs(self.modpm(x, self.q))

    #   Algorithm 35, Power2Round(r)
    #   "PowerTwoRound is applied componentwise."

    def power2round(self, r):
        r0vv = []
        r1vv = []
        for rr in r:
            r0v = []
            r1v = []
            for rx in rr:
                rp = rx % self.q
                r0 = self.modpm(rp, 1 << self.d)
                r1 = (rp - r0) >> self.d
                r0v += [r0]
                r1v += [r1]
            r0vv += [r0v]
            r1vv += [r1v]
        return r1vv, r0vv

    #   Algorithm 36, Decompose(r)

    def decompose(self, r):
        rp = r % self.q
        r0 = self.modpm(rp, 2 * self.gam2)
        if rp - r0 == self.q - 1:
            r1 = 0
            r0 -= 1
        else:
            r1 = (rp - r0) // (2 * self.gam2)
        return (r1, r0)

    #   Algorithm 37, HighBits(r)

    def high_bits(self, r):
        r1vv = []
        for rr in r:
            r1v = []
            for rx in rr:
                (r1, r0) = self.decompose(rx)
                r1v += [r1]
            r1vv += [r1v]
        return r1vv

    #   Algorithm 38, LowBits(r)

    def low_bits(self, r):
        r0vv = []
        for rr in r:
            r0v = []
            for rx in rr:
                (r1, r0) = self.decompose(rx)
                r0v += [r0]
            r0vv += [r0v]
        return r0vv

    #   Algorithm 39, MakeHint(z, r)

    def make_hint(self, z, r):
        r1 = self.high_bits(r)
        v1 = self.high_bits(self.add(r, z))
        return self.neq(r1, v1)

    #   Algorithm 40, UseHint(h, r)

    def use_hint(self, h, r):
        if isinstance(h[0], list):
            return [self.use_hint(h[i], r[i]) for i in range(len(h))]
        m = (self.q - 1) // (2 * self.gam2)
        r1v = []
        for i in range(256):
            (r1, r0) = self.decompose(r[i])
            if h[i] == 1 and r0 > 0:
                r1 = (r1 + 1) % m
            if h[i] == 1 and r0 <= 0:
                r1 = (r1 - 1) % m
            r1v += [r1]
        return r1v

    #   Algorithm 41, NTT(w)

    def ntt(self, w):
        w = w.copy()
        m = 0
        le = 128
        while le >= 1:
            st = 0
            while st < 256:
                m += 1
                z = ML_DSA_ZETAS[m]
                for j in range(st, st + le):
                    t = (z * w[j + le]) % self.q
                    w[j + le] = (w[j] - t) % self.q
                    w[j] = (w[j] + t) % self.q
                st = st + 2 * le
            le = le // 2
        return w

    #   Algorithm 42, NTT^-1(w)

    def ntt_inverse(self, w):
        """Compute the inverse NTT of a polynomial.

        :param w: The weights.
        :return: The result of the inverse NTT.
        """
        w = w.copy()
        m = 256
        le = 1
        while le < 256:
            st = 0
            while st < 256:
                m -= 1
                z = -ML_DSA_ZETAS[m]
                for j in range(st, st + le):
                    t = w[j]
                    w[j] = (t + w[j + le]) % self.q
                    w[j + le] = (t - w[j + le]) % self.q
                    w[j + le] = (z * w[j + le]) % self.q
                st = st + 2 * le
            le = 2 * le
        f = 8347681
        w = [(f * w[j]) % self.q for j in range(256)]
        return w

    #   Algorithm 43, BitRev8(m)

    def bitrev8(self, m):
        b = self.integer_to_bits(m, 8)
        brev = [b[7 - i] for i in range(8)]
        r = self.bits_to_integer(brev, 8)
        return r

    #   Algorithm 44, AddNTT(a, b)

    def add(self, a, b):
        if isinstance(a, list):
            return [self.add(a[i], b[i]) for i in range(len(a))]
        else:
            return (a + b) % self.q

    #   negation

    def neg(self, a):
        """Com

        :param a:
        :return:
        """
        if isinstance(a, list):
            return [self.neg(a[i]) for i in range(len(a))]
        else:
            return (-a) % self.q

    #   subtraction

    def sub(self, a, b):
        """Compute the subtraction of two values inside the polynomial ring.

        :param a: The first value.
        :param b: The second value.
        :return: The result of the subtraction.
        """
        if isinstance(a, list):
            return [self.sub(a[i], b[i]) for i in range(len(a))]
        else:
            return (a - b) % self.q

    #   not equivalent

    def neq(self, a, b):
        """Compute the not equivalent of two values.

        :param a: The first value.
        :param b: The second value.
        :return: The result of the not equivalent operation.
        """
        if isinstance(a, list):
            return [self.neq(a[i], b[i]) for i in range(len(a))]
        elif a == b:
            return 0
        else:
            return 1

    #   weight (number of nonzero entries)

    def weight(self, a):
        if isinstance(a, list):
            w = 0
            for ai in a:
                w += self.weight(ai)
            return w
        elif a == 0:
            return 0
        else:
            return 1

    #   Algorithm 45, MulNTT(a, b)

    def mul_ntt(self, a, b):
        return [(a[i] * b[i]) % self.q for i in range(256)]

    #   Algorithm 48, MatrixVectorNTT(M^, v^)

    def matrix_vector_ntt(self, m, v):
        w = [[0] * 256 for _ in range(self.k)]
        for i in range(self.k):
            for j in range(self.ell):
                w[i] = self.add(w[i], self.mul_ntt(m[i][j], v[j]))
        return w
