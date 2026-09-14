# <cryptographic_providers>

Which provider supplies what, and which are in scope. Primitive definitions are in
[primitives.md](primitives.md).

---

## Scope

| Provider | Installed | Status |
|---|---|---|
| `AndroidOpenSSL` | device | benchmarked |
| `AndroidKeyStore` + `AndroidKeyStoreBCWorkaround` | device | benchmarked |
| `Conscrypt` (`org.conscrypt:conscrypt-android`) | bundle in APK | candidate |
| Bouncy Castle (`org.bouncycastle:bcprov-jdk18on`) | bundle in APK | candidate |
| `BC` (platform) | device | excluded |
| `Crypto` | — | not present on Android |

An unqualified `getInstance` resolves to `AndroidOpenSSL`.

---

## AndroidOpenSSL

### Supports

| Service | Algorithms |
|---|---|
| Cipher | AES/{ECB,CBC}/{NoPadding,PKCS5Padding}, AES/CTR/NoPadding, AES/GCM/NoPadding, AES/GCM-SIV/NoPadding, AES_{128,256} variants, ChaCha20, ChaCha20/Poly1305/NoPadding, DESEDE/CBC/{NoPadding,PKCS5Padding}, ARC4, RSA/ECB/{NoPadding,PKCS1Padding,OAEPPadding,OAEPWithSHA-{1,224,256,384,512}AndMGF1Padding} |
| MessageDigest | MD5, SHA-1, SHA-224, SHA-256, SHA-384, SHA-512 |
| Mac | HmacMD5, HmacSHA{1,224,256,384,512}, AESCMAC |
| Signature | MD5withRSA, SHA{1,224,256,384,512}withRSA, SHA{1,224,256,384,512}withRSA/PSS, NONEwithECDSA, SHA{1,224,256,384,512}withECDSA, EdDSA, ML-DSA-{44,65,87}, SLH-DSA-SHA2-128S, MLDSA*-hybrids |
| KeyGenerator | AES, ARC4, ChaCha20, DESEDE, HmacMD5, HmacSHA{1,224,256,384,512} |
| KeyPairGenerator | RSA, EC, EdDSA, XDH, ML-DSA-*, ML-KEM-{768,1024}, SLH-DSA-SHA2-128S, XWING |
| KeyAgreement | XDH (X25519) |

### Does not support

Single DES, Blowfish, RC2, DSA, DESEDE/ECB, AES OFB/CFB, PKCS7Padding as distinct
code (aliased to PKCS5Padding), keys of 512 bits.

---

## AndroidKeyStore + AndroidKeyStoreBCWorkaround

### Supports

| Service | Algorithms |
|---|---|
| KeyStore | AndroidKeyStore |
| KeyPairGenerator / KeyFactory | RSA, EC, XDH, ED25519, ML-DSA-{65,87} |
| KeyGenerator / SecretKeyFactory | AES, DESede, HmacSHA{1,224,256,384,512} |
| Cipher | AES/{ECB,CBC,CTR,GCM}, DESede, RSA (PKCS1, OAEP) |
| Signature | RSA, ECDSA, ML-DSA-{65,87} |
| Mac | HmacSHA{1,224,256,384,512} |
| KeyAgreement | ECDH, XDH |

### StrongBox subset

RSA 2048, AES 128/256, ECDSA P-256, ECDH P-256, HMAC-SHA256 (8–64 byte keys),
Triple DES.

### Does not support

Key export, raw key material access, ChaCha20, arbitrary EC curves under StrongBox.

---

## Candidates

| Provider | Adds | Notes |
|---|---|---|
| `Conscrypt` bundled | a newer BoringSSL than the device's | same API as `AndroidOpenSSL`; register under its own name |
| Bouncy Castle bundled | full algorithm set: DES, Blowfish, DSA, SHA-3, Argon2, extended modes and paddings | provider name `BC` clashes with the platform copy; register under another name |
