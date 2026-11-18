# Primitives

## Configured test set

`config/testsets/predefined.yaml`, the test set of `config/global.yaml`. Field rules: `apps/benchmark/modules/config/docs/config.md`.

| part | providers | primitives |
|---|---|---|
| tier 1 | AndroidOpenSSL, BundledConscrypt, BundledBC, AndroidKeyStore | AES-CBC, AES-GCM, SHA-256, SHA-1, MD5, HmacSHA256, RSA OAEP-SHA256 and PKCS#1, SHA256withRSA, AES and RSA key generation; StrongBox AES and RSA-2048 |
| tier 2 | same | ECDSA P-256 and P-384, Ed25519, ECDH P-256 and P-384, X25519, their key generation; StrongBox P-256 |
| tier 3 | same | SHA-512, HmacSHA1, HmacSHA512, RSA-3072, ChaCha20-Poly1305, AES-CTR, BundledBC RSASSA-PSS |
| tier 4 | same | SHA-384, HmacSHA384, RSA-4096, DESede-CBC |
| breadth | AndroidOpenSSL, BundledConscrypt, BundledBC, platform BC | SHA-224, HmacSHA224, AES-GCM-SIV, P-521, FFDH-2048 |
| BouncyCastle only | BundledBC | SHA-3, HMAC-SHA3, Ed448, X448, SLH-DSA 128f and SHAKE |
| legacy | AndroidOpenSSL, BundledConscrypt, BundledBC, platform BC | ARC4, HmacMD5, DSA-2048, DH-1024 as group `modp1024` |
| post-quantum | AndroidOpenSSL, BundledConscrypt, BundledBC | ML-DSA, ML-KEM key generation, SLH-DSA-SHA2-128s |
| AndroidKeyStore | AndroidKeyStore | DESede, HmacSHA1–512, P-521, ML-DSA key generation; StrongBox RSA-3072/4096, P-384, Ed25519, X25519, DESede, HmacSHA256 |
| remaining | any | one rule per JCA type: every other inventory primitive at provider-chosen parameters |

- A primitive named in a tier takes the tier's settings.
- `exclude` is empty.

## Observed per provider

Device data; devices in [providers.md](providers.md).

| primitive | provider | JCA type | use |
|---|---|---|---|
| AES/GCM/NoPadding | AndroidOpenSSL | Cipher | bulk encryption with integrity |
| AES/GCM-SIV/NoPadding | AndroidOpenSSL | Cipher | bulk encryption, survives IV reuse |
| AES/CBC/{NoPadding,PKCS5Padding} | AndroidOpenSSL | Cipher | bulk encryption, no integrity |
| AES/ECB/{NoPadding,PKCS5Padding} | AndroidOpenSSL | Cipher | single block; leaks patterns |
| AES/CTR/NoPadding | AndroidOpenSSL | Cipher | stream-style bulk encryption |
| AES_{128,256}/… | AndroidOpenSSL | Cipher | key-size-pinned variants |
| ChaCha20 | AndroidOpenSSL | Cipher | bulk encryption without AES hardware |
| ChaCha20/Poly1305/NoPadding | AndroidOpenSSL | Cipher | as above, with integrity |
| DESEDE/CBC/{NoPadding,PKCS5Padding} | AndroidOpenSSL | Cipher | legacy interop |
| ARC4 | AndroidOpenSSL | Cipher | legacy interop; broken |
| AES/{ECB,CBC,CTR,GCM}, DESede | AndroidKeyStoreBCWorkaround | Cipher | bulk encryption under a hardware key |
| RSA/ECB/OAEPPadding, OAEPWithSHA-{1,224,256,384,512}AndMGF1Padding | AndroidOpenSSL | Cipher | key transport, small payloads |
| RSA/ECB/{NoPadding,PKCS1Padding} | AndroidOpenSSL | Cipher | legacy key transport |
| RSA (PKCS1, OAEP) | AndroidKeyStoreBCWorkaround | Cipher | key transport under a hardware key |
| SHA-{1,224,256,384,512}, MD5 | AndroidOpenSSL | MessageDigest | fingerprints, HMAC and signature input |
| HmacSHA{1,224,256,384,512}, HmacMD5 | AndroidOpenSSL | Mac | integrity tag with a shared key |
| AESCMAC | AndroidOpenSSL | Mac | integrity tag from a block cipher |
| HmacSHA{1,224,256,384,512} | AndroidKeyStore | Mac | integrity tag under a hardware key |
| SHA{1,224,256,384,512}withRSA, MD5withRSA | AndroidOpenSSL | Signature | authenticity with an RSA key |
| SHA{1,224,256,384,512}withRSA/PSS | AndroidOpenSSL | Signature | as above, PSS padding |
| SHA{1,224,256,384,512}withECDSA, NONEwithECDSA | AndroidOpenSSL | Signature | authenticity with a small EC key |
| EdDSA (Ed25519) | AndroidOpenSSL | Signature | authenticity, deterministic nonce |
| ML-DSA-{44,65,87}, SLH-DSA-SHA2-128S, MLDSA*-hybrids | AndroidOpenSSL | Signature | post-quantum authenticity |
| RSA, ECDSA | AndroidKeyStoreBCWorkaround | Signature | authenticity with a hardware key |
| ML-DSA-{65,87} | AndroidKeyStore | Signature | post-quantum, hardware key |
| ML-KEM-{768,1024}, XWING | AndroidOpenSSL | KeyPairGenerator (KEM) | post-quantum shared secret |
| XDH (X25519) | AndroidOpenSSL | KeyAgreement | shared secret between two parties |
| ECDH, XDH | AndroidKeyStore | KeyAgreement | shared secret with a hardware key |
| AES, ARC4, ChaCha20, DESEDE, Hmac* | AndroidOpenSSL | KeyGenerator | make a secret key |
| AES, HmacSHA*, DESede | AndroidKeyStore | KeyGenerator | make a non-exportable hardware key |
| RSA, EC, EdDSA, XDH, ML-*, XWING | AndroidOpenSSL | KeyPairGenerator | make a key pair |
| RSA, EC, XDH, ED25519 | AndroidKeyStore | KeyPairGenerator | make a hardware key pair |

## Observed usage rules

| rule | applies to |
|---|---|
| AES keys are 128, 192 or 256 bits | AndroidOpenSSL KeyGenerator |
| GCM takes a 12-byte IV via `GCMParameterSpec` | AES/GCM, AES/GCM-SIV |
| `PKCS7Padding` resolves to the `PKCS5Padding` code | AndroidOpenSSL ciphers |
| 512-bit keys are rejected | AndroidOpenSSL |
