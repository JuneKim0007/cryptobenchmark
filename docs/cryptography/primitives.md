# <cryptographic_primitives>

Cryptographic primitives, the providers that supply them, and what each is for.
Provider support: [providers.md](providers.md).

Devices: Pixel 9 (Tensor G4), Pixel 10 (Tensor G5), Android 17 (API 37), baseline
Android 16 (API 36). Titan M2 backs StrongBox keys.

---

## Types

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


---

## Providers

| Provider | Description |
|---|---|
| `AndroidOpenSSL` | Android SDK native provider for general-purpose cryptography |
| `AndroidKeyStore` + `AndroidKeyStoreBCWorkaround` | Android SDK native provider for hardware-backed keys |

Non-native, bundled in the APK: Conscrypt (`org.conscrypt:conscrypt-android`),
Bouncy Castle (`org.bouncycastle:bcprov-jdk18on`).

---

## List

`bench` = measured by the current suite.

| Cryptography | Provider | Type | Use | bench |
|---|---|---|---|---|
| AES/GCM/NoPadding | AndroidOpenSSL | symmetric-cipher | bulk encryption with integrity | yes |
| AES/GCM-SIV/NoPadding | AndroidOpenSSL | symmetric-cipher | bulk encryption, survives IV reuse | yes |
| AES/CBC/{NoPadding,PKCS5Padding} | AndroidOpenSSL | symmetric-cipher | bulk encryption, no integrity | yes |
| AES/ECB/{NoPadding,PKCS5Padding} | AndroidOpenSSL | symmetric-cipher | single block; leaks patterns | yes |
| AES/CTR/NoPadding | AndroidOpenSSL | symmetric-cipher | stream-style bulk encryption | yes |
| AES_{128,256}/… | AndroidOpenSSL | symmetric-cipher | key-size-pinned variants | no |
| ChaCha20 | AndroidOpenSSL | symmetric-cipher | bulk encryption without AES hardware | yes |
| ChaCha20/Poly1305/NoPadding | AndroidOpenSSL | symmetric-cipher | as above, with integrity | no |
| DESEDE/CBC/{NoPadding,PKCS5Padding} | AndroidOpenSSL | symmetric-cipher | legacy interop | yes |
| ARC4 | AndroidOpenSSL | symmetric-cipher | legacy interop; broken | yes |
| AES/{ECB,CBC,CTR,GCM}, DESede | AndroidKeyStoreBCWorkaround | symmetric-cipher | bulk encryption under a hardware key | yes |
| RSA/ECB/OAEPPadding, OAEPWithSHA-{1,224,256,384,512}AndMGF1Padding | AndroidOpenSSL | asymmetric-cipher | key transport / small payloads | yes |
| RSA/ECB/{NoPadding,PKCS1Padding} | AndroidOpenSSL | asymmetric-cipher | legacy key transport | yes |
| RSA (PKCS1, OAEP) | AndroidKeyStoreBCWorkaround | asymmetric-cipher | key transport under a hardware key | yes |
| SHA-{1,224,256,384,512}, MD5 | AndroidOpenSSL | hash | fingerprints, HMAC and signature input | yes |
| HmacSHA{1,224,256,384,512}, HmacMD5 | AndroidOpenSSL | mac | integrity tag with a shared key | yes |
| AESCMAC | AndroidOpenSSL | mac | integrity tag from a block cipher | no |
| HmacSHA{1,224,256,384,512} | AndroidKeyStore | mac | integrity tag under a hardware key | no |
| SHA{1,224,256,384,512}withRSA, MD5withRSA | AndroidOpenSSL | signature | authenticity with an RSA key | yes |
| SHA{1,224,256,384,512}withRSA/PSS | AndroidOpenSSL | signature | as above, modern padding | no |
| SHA{1,224,256,384,512}withECDSA, NONEwithECDSA | AndroidOpenSSL | signature | authenticity with a small EC key | **no** |
| EdDSA (Ed25519) | AndroidOpenSSL | signature | authenticity, deterministic nonce | no |
| ML-DSA-{44,65,87}, SLH-DSA-SHA2-128S, MLDSA*-hybrids | AndroidOpenSSL | signature | post-quantum authenticity | no |
| RSA, ECDSA | AndroidKeyStoreBCWorkaround | signature | authenticity with a hardware key | yes (RSA) |
| ML-DSA-{65,87} | AndroidKeyStore | signature | post-quantum, hardware key | no |
| ML-KEM-{768,1024}, XWING | AndroidOpenSSL | kem | post-quantum shared secret | no |
| XDH (X25519) | AndroidOpenSSL | key-agreement | shared secret between two parties | no |
| ECDH, XDH | AndroidKeyStore | key-agreement | shared secret with a hardware key | no |
| KeyGenerator: AES, ARC4, ChaCha20, DESEDE, Hmac* | AndroidOpenSSL | keygen-symmetric | make a secret key | yes |
| KeyGenerator: AES, HmacSHA*, DESede | AndroidKeyStore | keygen-symmetric | make a non-exportable hardware key | yes (AES) |
| KeyPairGenerator: RSA, EC, EdDSA, XDH, ML-*, XWING | AndroidOpenSSL | keygen-asymmetric | make a key pair | yes (RSA) |
| KeyPairGenerator: RSA, EC, XDH, ED25519 | AndroidKeyStore | keygen-asymmetric | make a hardware key pair | yes (RSA) |

No provider here supplies: single DES, Blowfish, DSA, DESEDE/ECB, AES OFB/CFB, RC2.

---

## Usage rules

| Rule | Applies to |
|---|---|
| AES keys are 128, 192 or 256 bits — nothing else | AndroidOpenSSL KeyGenerator |
| GCM needs a 12-byte IV, passed via `GCMParameterSpec` | AES/GCM, AES/GCM-SIV |
| `PKCS7Padding` resolves to the same code as `PKCS5Padding` | all Conscrypt ciphers |
| 512-bit keys are rejected | all AndroidOpenSSL |

### Benchmark scope

Measured: AES/GCM/NoPadding (12-byte IV), AES/CBC/PKCS5Padding, AES/CTR/NoPadding, ChaCha20,
ChaCha20-Poly1305, RSA/ECB/OAEP*, RSA/ECB/PKCS1Padding, SHA-1/256/512, HmacSHA1/256, SHA256withRSA,
SHA256withECDSA, and key generation for each. Baselines only: MD5, 3DES, RC4.
Out of scope: ML-DSA, ML-KEM, SLH-DSA, HPKE, X25519, ECDH, XDH, AES-CMAC, AES/GCM-SIV, Ed25519, DES, Blowfish, DSA.

### Key sizes

| Algorithm | Sizes (bits) |
|---|---|
| AES | 128, 192, 256 |
| DESEDE | 112, 168 |
| ARC4 | variable, 40–2048 typical |
| ChaCha20 | 256 |
| HMAC-SHA* | 64–512 |
| RSA | 2048, 4096 — StrongBox: 2048 only |
| ECDSA / ECDH | P-256 — StrongBox: P-256 only |

