# <cryptographic_primitives>

Catalogue of cryptographic primitives and the providers that supply them. Scope —
which of these are benchmarked — is in the [README](../../README.md).

**Target:** Pixel 9 (Tensor G4) and Pixel 10 (Tensor G5), Android 17 (API 37,
released June 2026). Baseline for comparison is Android 16 (API 36), the most-used
version worldwide at ~22–25%. Both carry the Titan M2 chip for StrongBox keys.

---

## Types

A hash has no key; asymmetric means a key pair. They are not the same family.

| Type | Key material | Direction |
|---|---|---|
| `symmetric-cipher` | one shared secret key | reversible with the same key |
| `asymmetric-cipher` | key pair: encrypt public, decrypt private | reversible with the other half |
| `signature` | key pair: sign private, verify public | one-way; verify returns a boolean |
| `hash` | none | one-way |
| `mac` | one shared secret key | one-way; check by recomputing |
| `kem` | key pair | produces a shared secret |
| `key-agreement` | key pair on both sides | produces a shared secret |
| `keygen-symmetric` | — | produces a secret key |
| `keygen-asymmetric` | — | produces a key pair |

### Curve names

| JCA name | Field prime | Curve | Scheme |
|---|---|---|---|
| `Ed25519` | 2^255 − 19 | edwards25519 (Edwards form) | EdDSA, SHA-512 fixed |
| `X25519` / `XDH` | 2^255 − 19 | Curve25519 (Montgomery form) | Diffie–Hellman |
| `SHA256withECDSA` | 2^256 − 2^224 + … − 1 | NIST P-256 / secp256r1 | ECDSA |

The `25519` is the prime 2^255 − 19. Ed25519 and X25519 are the same curve in two
equivalent forms, but sign and key-agree respectively. Against ECDSA P-256 the
difference is the scheme: EdDSA fixes its hash and derives the nonce
deterministically; ECDSA names its digest and needs a fresh random nonce per
signature.

---

## Providers

| Provider | What it is | Status |
|---|---|---|
| `AndroidOpenSSL` | Conscrypt / BoringSSL, the platform default; mainline module since Android 10 | current |
| `AndroidKeyStore` | key generation, storage, key factories for hardware-backed keys | current |
| `AndroidKeyStoreBCWorkaround` | cipher/signature/MAC operations on AndroidKeyStore keys; internal | current |
| `BC` (platform) | Android's stripped Bouncy Castle | **removed in Android 12** — deprecated in Android 9, implementations deleted in 12 "including all AES algorithms" |
| `BC` bundled (`org.bouncycastle:bcprov-jdk18on`) | full Bouncy Castle inside the APK; provider name `BC` clashes, register explicitly | candidate |
| `Conscrypt` bundled (`org.conscrypt:conscrypt-android`) | newer BoringSSL than the device's | candidate |

`Crypto` provider: removed in Android 9. Tink and Jetpack `security-crypto` are
libraries, not providers; `security-crypto` was deprecated in 2025.

### Conscrypt constraints (since Android 12)

| Constraint | Effect |
|---|---|
| 512-bit keys unsupported | any 512-bit case fails |
| `KeyGenerator` validates key size | AES accepts only 128/192/256; BC used to allow invalid sizes and fail later |
| GCM requires a 12-byte IV | a 16-byte IV fails; NIST-recommended length is enforced |
| `PKCS7Padding` is an **alias** of `PKCS5Padding` | both names reach identical code — benchmarking both measures the same thing twice |

---

## List — AndroidOpenSSL (Conscrypt)

Verified against upstream `OpenSSLProvider.java`. Everything registered, in scope or
not; `bench` = measured by the current suite.

| Cryptography | Type | Status | bench |
|---|---|---|---|
| AES/ECB/{NoPadding,PKCS5Padding} | symmetric-cipher | current | yes |
| AES/CBC/{NoPadding,PKCS5Padding} | symmetric-cipher | current | yes |
| AES/CTR/NoPadding | symmetric-cipher | current | yes |
| AES/GCM/NoPadding | symmetric-cipher | current | yes |
| AES/GCM-SIV/NoPadding | symmetric-cipher | current, out-of-scope | yes |
| AES_{128,256}/{ECB,CBC,GCM,GCM-SIV}/… | symmetric-cipher | current, key-size-pinned variants | no |
| ChaCha20 | symmetric-cipher | current | yes |
| ChaCha20/Poly1305/NoPadding | symmetric-cipher (AEAD) | current | no |
| DESEDE/CBC/{NoPadding,PKCS5Padding} | symmetric-cipher | legacy-algorithm | yes |
| ARC4 | symmetric-cipher | legacy-algorithm | yes |
| RSA/ECB/{NoPadding,PKCS1Padding} | asymmetric-cipher | legacy-algorithm | yes |
| RSA/ECB/OAEPPadding, OAEPWithSHA-{1,224,256,384,512}AndMGF1Padding | asymmetric-cipher | current | yes |
| SHA-{1,224,256,384,512}, MD5 | hash | current (MD5, SHA-1 legacy) | yes |
| HmacSHA{1,224,256,384,512}, HmacMD5 | mac | current (MD5 legacy) | yes |
| AESCMAC | mac | current, out-of-scope | no |
| SHA{1,224,256,384,512}withRSA, MD5withRSA | signature | current (MD5, SHA-1 legacy) | yes |
| SHA{1,224,256,384,512}withRSA/PSS | signature | current | no |
| SHA{1,224,256,384,512}withECDSA, NONEwithECDSA | signature | current | **no** |
| EdDSA (Ed25519) | signature | current, out-of-scope | no |
| ML-DSA-{44,65,87}, SLH-DSA-SHA2-128S, MLDSA*-hybrids | signature | current, out-of-scope | no |
| ML-KEM-{768,1024}, XWING | kem | current, out-of-scope | no |
| XDH (X25519) | key-agreement | current, out-of-scope | no |
| KeyGenerator: AES, ARC4, ChaCha20, DESEDE, Hmac{MD5,SHA1,SHA224,SHA256,SHA384,SHA512} | keygen-symmetric | current | yes |
| KeyPairGenerator: RSA, EC, EdDSA, XDH, ML-*, XWING | keygen-asymmetric | current | yes (RSA) |

**Not in Conscrypt at all:** DES (single), Blowfish, DSA, DESEDE/ECB, AES OFB/CFB
modes, RC2.

## List — AndroidKeyStore / AndroidKeyStoreBCWorkaround

| Cryptography | Type | Status | bench |
|---|---|---|---|
| AES/{ECB,CBC,CTR,GCM} | symmetric-cipher | current | yes |
| DESede | symmetric-cipher | legacy-algorithm | yes |
| RSA (PKCS1, OAEP) | asymmetric-cipher | current | yes |
| RSA, ECDSA signatures | signature | current | yes (RSA) |
| HmacSHA{1,224,256,384,512} | mac | current | no |
| ML-DSA-{65,87} | signature | current (Android 17), out-of-scope | no |
| ECDH, XDH | key-agreement | current, out-of-scope | no |
| KeyPairGenerator: RSA, EC, XDH, ED25519 | keygen-asymmetric | current | yes (RSA) |
| KeyGenerator: AES, HmacSHA*, DESede | keygen-symmetric | current | yes (AES) |

**StrongBox (Titan M2) subset:** RSA 2048 only, AES 128/256, ECDSA P-256, ECDH
P-256, HMAC-SHA256 (8–64 byte keys), Triple DES.

---

## Removed — replace with

Benchmarked today, no provider on the target devices. Replace, do not keep failing.

| Current | Why gone | Replacement |
|---|---|---|
| BC: SHA-*, MD5 digests | BC removed in Android 12 | same digests on AndroidOpenSSL |
| BC: HmacSHA*, HmacMD5 | BC removed in Android 12 | same on AndroidOpenSSL |
| BC: SHA*withRSA | BC removed in Android 12 | same on AndroidOpenSSL |
| BC: SHA*withDSA / DSA keygen | BC removed; Conscrypt has no DSA | **SHA256withECDSA** (P-256) |
| BC: DES/{ECB,CBC,CTR,OFB}/* | no DES in Conscrypt | DESEDE/CBC for a legacy baseline, else drop |
| BC: Blowfish | no Blowfish in Conscrypt | drop, or bundled BC |
| BC: ARC4 | cipher removed from BC | ARC4 on AndroidOpenSSL |
| AndroidOpenSSL: SHA*withDSA | Conscrypt never registered DSA | SHA*withECDSA |
| 3DES/CBC/PKCS7Padding, AES/*/PKCS7Padding | alias of PKCS5Padding | keep PKCS5Padding only |
| DESEDE/ECB (keystore tests) | Conscrypt registers CBC only | DESEDE/CBC |
| AES keys 40/56/168 bits | Conscrypt rejects invalid AES sizes | AES 128/192/256; keep 56 for DES-family only |
| AES/GCM with 16-byte IV | Conscrypt requires 12 bytes | 12-byte IV via `GCMParameterSpec` |
| RSA/DSA 1024-bit | below current guidance; StrongBox needs 2048 | RSA 2048/4096 |

---

## Device probe

Rows come from provider source and docs. Ground truth is the device: an instrumented
test that walks `Security.getProviders()` and records every service, algorithm and
alias as JSON per device and Android version. It replaces the hand-written
`app/src/main/res/raw/device_primitives.json` and `restrictions.json`, and lets an
absent algorithm be recorded as **unsupported** rather than failed.
