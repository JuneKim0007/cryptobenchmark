# <cryptographic_primitives>

Catalogue of cryptographic primitives and the providers that supply them on current
Android. Scope — which of these are actually benchmarked — is in the
[README](../../README.md).

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
| `BC` (platform) | Android's stripped Bouncy Castle | legacy — deprecated Android 9, most algorithms since deleted |
| `BC` bundled (`org.bouncycastle:bcprov-jdk18on`) | full Bouncy Castle inside the APK; provider name `BC` clashes, register explicitly | candidate |
| `Conscrypt` bundled (`org.conscrypt:conscrypt-android`) | newer BoringSSL than the device's | candidate |

`Crypto` provider: removed in Android 9. Tink and Jetpack `security-crypto` are
libraries, not providers; `security-crypto` was deprecated in 2025.

---

## List

`bench` = measured by the current suite. `verified` = read in provider source;
`inferred` = from docs or the same removal list; `unverified` = needs the device probe.

| Cryptography | Provider | Type | Status | Evidence | bench |
|---|---|---|---|---|---|
| AES/ECB/{NoPadding,PKCS5Padding,PKCS7Padding} | AndroidOpenSSL | symmetric-cipher | current | verified | yes |
| AES/CBC/{NoPadding,PKCS5Padding,PKCS7Padding} | AndroidOpenSSL | symmetric-cipher | current | verified | yes |
| AES/CTR/NoPadding | AndroidOpenSSL | symmetric-cipher | current | verified | yes |
| AES/GCM/NoPadding | AndroidOpenSSL | symmetric-cipher | current | verified | yes |
| AES/GCM-SIV/NoPadding | AndroidOpenSSL | symmetric-cipher | current, out-of-scope | verified | yes |
| ChaCha20 | AndroidOpenSSL | symmetric-cipher | current | verified | yes |
| DESede (3DES) /CBC/{NoPadding,PKCS5Padding,PKCS7Padding} | AndroidOpenSSL | symmetric-cipher | legacy-algorithm | verified | yes |
| ARC4 (RC4) | AndroidOpenSSL | symmetric-cipher | legacy-algorithm | verified | yes |
| AES/{ECB,CTR,GCM}/NoPadding | AndroidKeyStoreBCWorkaround | symmetric-cipher | current | inferred | yes |
| DESede/ECB/{NoPadding,PKCS7Padding} | AndroidKeyStoreBCWorkaround | symmetric-cipher | legacy-algorithm | inferred | yes |
| AES (ECB only) | BC platform | symmetric-cipher | legacy | verified | no |
| DES (ECB only) | BC platform | symmetric-cipher | legacy | verified | partly |
| RSA/ECB/PKCS1Padding | AndroidOpenSSL | asymmetric-cipher | legacy-algorithm | verified | yes |
| RSA/ECB/OAEPPadding | AndroidOpenSSL | asymmetric-cipher | current | verified | yes |
| RSA/ECB/OAEPwithSHA-{1,224,256,384,512}andMGF1Padding | AndroidOpenSSL | asymmetric-cipher | current | verified | yes |
| RSA/ECB/{PKCS1,OAEPwithSHA-1/224/256}Padding | AndroidKeyStoreBCWorkaround | asymmetric-cipher | current | inferred | yes |
| SHA-{1,224,256,384,512} | AndroidOpenSSL | hash | current | verified | yes |
| MD5 | AndroidOpenSSL | hash | legacy-algorithm | verified | yes |
| HmacSHA-{1,224,256,384,512} | AndroidOpenSSL | mac | current | inferred | yes |
| HmacMD5 | AndroidOpenSSL | mac | legacy-algorithm | verified | yes |
| AES-CMAC | AndroidOpenSSL | mac | current, out-of-scope | inferred (Android 14) | no |
| SHA{1,224,256,384,512}withRSA | AndroidOpenSSL | signature | current | verified | yes |
| SHA{1,224,256,384,512}withECDSA | AndroidOpenSSL | signature | current | inferred | **no** |
| Ed25519 | AndroidOpenSSL | signature | current, out-of-scope | verified | no |
| ML-DSA-{44,65,87} | AndroidOpenSSL | signature | current, out-of-scope | verified (upstream Conscrypt) | no |
| SLH-DSA-SHA2-128S | AndroidOpenSSL | signature | current, out-of-scope | verified (upstream Conscrypt) | no |
| ML-DSA-{65,87} | AndroidKeyStore | signature | current (Android 17), out-of-scope | documented | no |
| SHA1withDSA | BC platform | signature | legacy | verified | yes |
| ML-KEM-{768,1024} | AndroidOpenSSL | kem | current, out-of-scope | keygen verified; encapsulation unverified | no |
| X25519 | AndroidOpenSSL | key-agreement | current, out-of-scope | verified | no |
| ECDH, XDH | AndroidKeyStore | key-agreement | current, out-of-scope | verified | no |
| HPKE | AndroidOpenSSL | kem + cipher | current, out-of-scope | verified | no |
| AES / HmacSHA* / DESede keygen | AndroidKeyStore | keygen-symmetric | current | verified | yes (AES) |
| AES, DES, DESede, Blowfish, ARC4, ChaCha20 keygen | AndroidOpenSSL | keygen-symmetric | current | inferred | yes |
| ARC4 keygen (cipher removed) | BC platform | keygen-symmetric | legacy | verified | no |
| RSA / EC / XDH / ED25519 keypair gen | AndroidKeyStore | keygen-asymmetric | current | verified | yes (RSA) |
| RSA keypair gen | AndroidOpenSSL | keygen-asymmetric | current | verified | yes |
| DSA keypair gen | BC platform | keygen-asymmetric | legacy | verified | yes |

---

## Legacy — pending sweep

Benchmarked today, gone or going from the platform. Delete the matching tests rather
than leave them failing.

| Cryptography | Provider | Type | What happened |
|---|---|---|---|
| SHA-{1,224,256,384,512}, MD5 | BC platform | hash | removed from source (`Android-removed`); verified for SHA-256 |
| HmacSHA*, HmacMD5 | BC platform | mac | removed; only a private HMAC-SHA256 for PBKDF2 remains |
| SHA{1,224,256,384,512}withRSA | BC platform | signature | on the Android 9 deprecation list; fails on Android 12+ |
| SHA{224,256,384,512}withDSA | BC platform | signature | removed from source |
| ARC4 cipher | BC platform | symmetric-cipher | cipher removed, keygen kept |
| DES/{CBC,CTR,OFB}/* | BC platform | symmetric-cipher | only `Cipher.DES` (ECB) remains |
| Blowfish | BC platform | symmetric-cipher | unverified — confirm with the device probe |
| SHA{1,224,256,384,512}withDSA | AndroidOpenSSL | signature | Conscrypt registers no DSA at all; probably never valid |
| `Crypto` provider | — | — | removed in Android 9 |

`targetSdkVersion 27` does not protect against this. It only stopped Android 9 from
rejecting deprecated BC calls; the implementations have since been deleted.

---

## Device probe

Rows above come from provider source and docs. Ground truth is the device: an
instrumented test that walks `Security.getProviders()` and records every service,
algorithm and alias as JSON per device and Android version. It replaces the
hand-written `app/src/main/res/raw/device_primitives.json` and `restrictions.json`,
and lets an absent algorithm be recorded as **unsupported** rather than failed.
