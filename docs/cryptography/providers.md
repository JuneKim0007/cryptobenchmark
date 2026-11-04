# Providers

## Observed devices

- Android 17 (API 37); baseline Android 16 (API 36).
- Primitive catalogue and scope: [primitives.md](primitives.md).

## Selection

- `config/testsets/scope.yaml` rules name no provider; every provider serving a matched name is selected.
- `exclude` is empty in `config/global.yaml` and `scope.yaml`; platform `BC` is selected wherever it serves a matched name.
- The APK bundles no crypto provider library; `:android` depends only on androidx benchmark and test libraries.

| provider | observed on device |
|---|---|
| `AndroidOpenSSL` | yes |
| `AndroidKeyStore` + `AndroidKeyStoreBCWorkaround` | yes |
| `BC` (platform) | yes |
| `Crypto` | no |

- An unqualified `getInstance` resolves to `AndroidOpenSSL`.

## AndroidOpenSSL

| service | algorithms |
|---|---|
| Cipher | AES/{ECB,CBC}/{NoPadding,PKCS5Padding}, AES/CTR/NoPadding, AES/GCM/NoPadding, AES/GCM-SIV/NoPadding, AES_{128,256} variants, ChaCha20, ChaCha20/Poly1305/NoPadding, DESEDE/CBC/{NoPadding,PKCS5Padding}, ARC4, RSA/ECB/{NoPadding,PKCS1Padding,OAEPPadding,OAEPWithSHA-{1,224,256,384,512}AndMGF1Padding} |
| MessageDigest | MD5, SHA-1, SHA-224, SHA-256, SHA-384, SHA-512 |
| Mac | HmacMD5, HmacSHA{1,224,256,384,512}, AESCMAC |
| Signature | MD5withRSA, SHA{1,224,256,384,512}withRSA, SHA{1,224,256,384,512}withRSA/PSS, NONEwithECDSA, SHA{1,224,256,384,512}withECDSA, EdDSA, ML-DSA-{44,65,87}, SLH-DSA-SHA2-128S, MLDSA*-hybrids |
| KeyGenerator | AES, ARC4, ChaCha20, DESEDE, HmacMD5, HmacSHA{1,224,256,384,512} |
| KeyPairGenerator | RSA, EC, EdDSA, XDH, ML-DSA-*, ML-KEM-{768,1024}, SLH-DSA-SHA2-128S, XWING |
| KeyAgreement | XDH (X25519) |

- Not supported: single DES, Blowfish, RC2, DSA, DESEDE/ECB, AES OFB/CFB.
- Usage rules: [primitives.md](primitives.md#observed-usage-rules).

## AndroidKeyStore + AndroidKeyStoreBCWorkaround

| service | algorithms |
|---|---|
| KeyStore | AndroidKeyStore |
| KeyPairGenerator, KeyFactory | RSA, EC, XDH, ED25519, ML-DSA-{65,87} |
| KeyGenerator, SecretKeyFactory | AES, DESede, HmacSHA{1,224,256,384,512} |
| Cipher | AES/{ECB,CBC,CTR,GCM}, DESede, RSA (PKCS1, OAEP) |
| Signature | RSA, ECDSA, ML-DSA-{65,87} |
| Mac | HmacSHA{1,224,256,384,512} |
| KeyAgreement | ECDH, XDH |

- StrongBox subset: RSA 2048, AES 128/256, ECDSA P-256, ECDH P-256, HMAC-SHA256 (8 to 64 byte keys), Triple DES.
- Not supported: key export, raw key material access, ChaCha20, arbitrary EC curves under StrongBox.
