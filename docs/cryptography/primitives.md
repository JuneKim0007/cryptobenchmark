# <cryptographic_primitives>

Catalogue of cryptographic primitives and the providers that supply them. Scope —
which of these are benchmarked — is in the [README](../../README.md).

**Target (as of 14 Sep 2026):** Pixel 9 (Tensor G4) and Pixel 10 (Tensor G5) on
**Android 17** (API 37, released June 2026) — the current release on both devices.
Comparison baseline is **Android 16** (API 36), the most-used version worldwide at
~22–25%. Both devices carry the Titan M2 chip for StrongBox keys.

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
| `BC` (platform) | Android's stripped Bouncy Castle | **reduced, not removed** — the algorithms Conscrypt duplicates were deleted in Android 12; block-cipher engines remain |
| `BC` bundled (`org.bouncycastle:bcprov-jdk18on`) | full Bouncy Castle inside the APK; provider name `BC` clashes, register explicitly | candidate |
| `Conscrypt` bundled (`org.conscrypt:conscrypt-android`) | newer BoringSSL than the device's | candidate |

`Crypto` provider: removed in Android 9. Tink and Jetpack `security-crypto` are
libraries, not providers; `security-crypto` was deprecated in 2025.

### Conscrypt constraints (since Android 12)

| Constraint | Kind | Effect |
|---|---|---|
| `KeyGenerator` validates key size | validation | AES accepts only 128/192/256; BC allowed invalid sizes and failed later at `Cipher` |
| 512-bit keys unsupported | validation | any 512-bit case fails |
| GCM requires a 12-byte IV | validation | a 16-byte IV fails; the NIST-recommended length is enforced |
| `PKCS7Padding` is an alias of `PKCS5Padding` | naming | not a restriction — both names reach identical code, so measuring both duplicates a row |

BC's extra "flexibility" was unvalidated input, not extra capability: keys of sizes
the cipher cannot use, and GCM IVs of lengths that weaken the mode. The only real
capability lost is 512-bit RSA.

### Valid key sizes

One key-size list swept across all algorithms is what produces invalid combinations.
Sizes are per algorithm.

| Algorithm | Sizes (bits) |
|---|---|
| AES | 128, 192, 256 |
| DESEDE (3DES) | 112, 168 |
| ARC4 | variable (40–2048 typical) |
| ChaCha20 | 256 |
| HMAC-SHA* | 64–512 (StrongBox: 64–512, i.e. 8–64 bytes) |
| RSA | 2048, 4096 (StrongBox: 2048 only) |
| ECDSA / ECDH | P-256 (StrongBox: P-256 only) |

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
modes, RC2. DES, DESEDE and Blowfish are still available from the platform `BC`
provider — see the BC list below.

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

## List — BC (platform)

Read from AOSP `external/bouncycastle` on `main`. Registering `Cipher.<algo>` gives
`<algo>/<mode>/<padding>` too: BC's generic block-cipher engine applies the mode and
padding, so DES/CBC/PKCS5Padding still resolves from a bare `Cipher.DES`.

| Cryptography | Type | Present | bench |
|---|---|---|---|
| Cipher.AES, AESWRAP | symmetric-cipher | yes (KeyGenerator.AES removed — generate the key elsewhere) | no |
| Cipher.DES, KeyGenerator.DES, SecretKeyFactory.DES | symmetric-cipher | yes | yes |
| Cipher.DESEDE, DESEDEWRAP | symmetric-cipher | yes | yes |
| Cipher.BLOWFISH, KeyGenerator.BLOWFISH | symmetric-cipher | yes | yes |
| KeyGenerator.ARC4 | keygen-symmetric | yes — but `Cipher.ARC4` is gone | yes |
| Signature.SHA1withDSA, KeyPairGenerator.DSA, KeyFactory.DSA | signature | yes | yes |
| PBE ciphers and secret-key factories | symmetric-cipher | yes | no |
| MessageDigest.* | hash | **no** | yes |
| Mac.Hmac* | mac | **no** | yes |
| Signature.SHA*withRSA, SHA*withECDSA | signature | **no** | yes |
| Signature.SHA{224,256,384,512}withDSA | signature | **no** | yes |
| Cipher.ARC4, AES/GCM | symmetric-cipher | **no** | yes |

`DEPRECATED_ALGORITHMS` in libcore now contains only `KEYFACTORY.RSA`; everything
else was deleted outright rather than blocked, so `targetSdk` no longer changes what
BC answers.

---

## Removed — replace with

Benchmarked today, no provider on the target devices. Replace, do not keep failing.

| Current | Why gone | Replacement |
|---|---|---|
| BC: SHA-*, MD5 digests | deleted from BC in Android 12 | same digests on AndroidOpenSSL |
| BC: HmacSHA*, HmacMD5 | deleted from BC | same on AndroidOpenSSL |
| BC: SHA*withRSA | deleted from BC | same on AndroidOpenSSL |
| BC: ARC4 cipher | cipher deleted; keygen kept | ARC4 on AndroidOpenSSL |
| BC: SHA{224,256,384,512}withDSA | deleted from BC | **SHA256withECDSA** (P-256) |
| AndroidOpenSSL: SHA*withDSA | Conscrypt never registered DSA | SHA*withECDSA |
| 3DES/CBC/PKCS7Padding, AES/*/PKCS7Padding | alias of PKCS5Padding | keep PKCS5Padding only |
| DESEDE/ECB on AndroidOpenSSL | Conscrypt registers CBC only | DESEDE/CBC, or keep ECB on BC |
| AES keys 40/56/168 bits | Conscrypt rejects invalid AES sizes | per-algorithm size lists — see Valid key sizes |
| AES/GCM with 16-byte IV | Conscrypt requires 12 bytes | 12-byte IV via `GCMParameterSpec` |
| RSA/DSA 1024-bit | below current guidance; StrongBox needs 2048 | RSA 2048/4096 |

Staying on BC: single DES, DESEDE, Blowfish and SHA1withDSA are still registered
there, so those tests keep their provider.

### Provider swap

| Primitive | Old provider | New provider |
|---|---|---|
| digests, HMACs, RSA signatures, ARC4 cipher | `BC` | `AndroidOpenSSL` |
| DESEDE keygen (`SymmetricKeyGen`) | `BC` | `AndroidOpenSSL` |
| single DES, DESEDE, Blowfish ciphers | `BC` | unchanged |
| symmetric cipher + keygen on hardware keys | `AndroidKeyStoreBCWorkaround` | unchanged |
| SHA{224,256,384,512}withDSA | `BC`, `AndroidOpenSSL` | ECDSA P-256 on `AndroidOpenSSL` |

Source to change: 4 live `"BC"` literals in `app/src/main` (`SymmetricDecrypt`,
`SymmetricKeyGen` ×2, `Digest`) and 121 in `app/src/androidTest`.

---

## Device probe

Rows come from provider source and docs. Ground truth is the device: an instrumented
test that walks `Security.getProviders()` and records every service, algorithm and
alias as JSON per device and Android version. It replaces the hand-written
`app/src/main/res/raw/device_primitives.json` and `restrictions.json`, and lets an
absent algorithm be recorded as **unsupported** rather than failed.
