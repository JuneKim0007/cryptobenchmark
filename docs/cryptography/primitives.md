# Primitives

## Configured scope

`config/testsets/scope.yaml`, the test set of `config/global.yaml`. Field rules: `apps/benchmark/modules/config/docs/config.md`.

| JCA type | name rule | key | parameters | role |
|---|---|---|---|---|
| Cipher | `AES/GCM/NoPadding` | AES 128, 192, 256 | `GCMParameterSpec(128, fresh(12))` | measured |
| Cipher | `AES/CBC/PKCS5Padding` | AES 128, 192, 256 | | measured |
| Cipher | `AES/CTR/NoPadding` | AES 128, 192, 256 | | measured |
| Cipher | `ChaCha20*` | | `ChaCha20`: `ChaCha20ParameterSpec(fresh(12), 1)` | measured |
| Cipher | `RSA/ECB/OAEP*` | RSA 2048, 4096; input 32 bytes | `OAEPWithSHA-256AndMGF1Padding`: `OAEPParameterSpec(SHA-256, MGF1, MGF1ParameterSpec.SHA256, PSpecified.DEFAULT)` | measured |
| Cipher | `RSA/ECB/PKCS1Padding` | RSA 2048, 4096; input 32 bytes | | measured |
| Cipher | `DESede/CBC/PKCS5Padding` | | | baseline (3DES) |
| Cipher | `ARCFOUR` | | | baseline (RC4) |
| MessageDigest | `SHA-256`, `SHA-1`, `SHA-512` | | | measured |
| MessageDigest | `MD5` | | | baseline |
| Mac | `HmacSHA256`, `HmacSHA1` | | | measured |
| Signature | `SHA256withRSA` | RSA 2048, 4096 | | measured |
| Signature | `SHA256withECDSA` | EC `secp256r1` | | measured |
| KeyGenerator | `AES` | 128, 192, 256 | | measured |
| KeyPairGenerator | `RSA` | 2048, 4096 | | measured |
| KeyPairGenerator | `EC` | `secp256r1` | | measured |

- Rules name no provider: every provider serving a matched name is selected.
- `exclude` is empty in `scope.yaml` and `global.yaml`.
- Out of scope: ML-DSA, ML-KEM, SLH-DSA, HPKE, X25519, ECDH, XDH, AES-CMAC, AES/GCM-SIV, Ed25519, DES, Blowfish, DSA.

## Observed per provider

Device data; devices in [providers.md](providers.md). `in scope` = the names a `scope.yaml` rule matches.

| primitive | provider | JCA type | use | in scope |
|---|---|---|---|---|
| AES/GCM/NoPadding | AndroidOpenSSL | Cipher | bulk encryption with integrity | yes |
| AES/GCM-SIV/NoPadding | AndroidOpenSSL | Cipher | bulk encryption, survives IV reuse | no |
| AES/CBC/{NoPadding,PKCS5Padding} | AndroidOpenSSL | Cipher | bulk encryption, no integrity | PKCS5Padding |
| AES/ECB/{NoPadding,PKCS5Padding} | AndroidOpenSSL | Cipher | single block; leaks patterns | no |
| AES/CTR/NoPadding | AndroidOpenSSL | Cipher | stream-style bulk encryption | yes |
| AES_{128,256}/… | AndroidOpenSSL | Cipher | key-size-pinned variants | no |
| ChaCha20 | AndroidOpenSSL | Cipher | bulk encryption without AES hardware | yes |
| ChaCha20/Poly1305/NoPadding | AndroidOpenSSL | Cipher | as above, with integrity | yes |
| DESEDE/CBC/{NoPadding,PKCS5Padding} | AndroidOpenSSL | Cipher | legacy interop | PKCS5Padding |
| ARC4 | AndroidOpenSSL | Cipher | legacy interop; broken | rule names `ARCFOUR` |
| AES/{ECB,CBC,CTR,GCM}, DESede | AndroidKeyStoreBCWorkaround | Cipher | bulk encryption under a hardware key | matching names |
| RSA/ECB/OAEPPadding, OAEPWithSHA-{1,224,256,384,512}AndMGF1Padding | AndroidOpenSSL | Cipher | key transport, small payloads | yes |
| RSA/ECB/{NoPadding,PKCS1Padding} | AndroidOpenSSL | Cipher | legacy key transport | PKCS1Padding |
| RSA (PKCS1, OAEP) | AndroidKeyStoreBCWorkaround | Cipher | key transport under a hardware key | matching names |
| SHA-{1,224,256,384,512}, MD5 | AndroidOpenSSL | MessageDigest | fingerprints, HMAC and signature input | SHA-1, SHA-256, SHA-512, MD5 |
| HmacSHA{1,224,256,384,512}, HmacMD5 | AndroidOpenSSL | Mac | integrity tag with a shared key | HmacSHA1, HmacSHA256 |
| AESCMAC | AndroidOpenSSL | Mac | integrity tag from a block cipher | no |
| HmacSHA{1,224,256,384,512} | AndroidKeyStore | Mac | integrity tag under a hardware key | HmacSHA1, HmacSHA256 |
| SHA{1,224,256,384,512}withRSA, MD5withRSA | AndroidOpenSSL | Signature | authenticity with an RSA key | SHA256withRSA |
| SHA{1,224,256,384,512}withRSA/PSS | AndroidOpenSSL | Signature | as above, PSS padding | no |
| SHA{1,224,256,384,512}withECDSA, NONEwithECDSA | AndroidOpenSSL | Signature | authenticity with a small EC key | SHA256withECDSA |
| EdDSA (Ed25519) | AndroidOpenSSL | Signature | authenticity, deterministic nonce | no |
| ML-DSA-{44,65,87}, SLH-DSA-SHA2-128S, MLDSA*-hybrids | AndroidOpenSSL | Signature | post-quantum authenticity | no |
| RSA, ECDSA | AndroidKeyStoreBCWorkaround | Signature | authenticity with a hardware key | matching names |
| ML-DSA-{65,87} | AndroidKeyStore | Signature | post-quantum, hardware key | no |
| ML-KEM-{768,1024}, XWING | AndroidOpenSSL | KeyPairGenerator (KEM) | post-quantum shared secret | no |
| XDH (X25519) | AndroidOpenSSL | KeyAgreement | shared secret between two parties | no |
| ECDH, XDH | AndroidKeyStore | KeyAgreement | shared secret with a hardware key | no |
| AES, ARC4, ChaCha20, DESEDE, Hmac* | AndroidOpenSSL | KeyGenerator | make a secret key | AES |
| AES, HmacSHA*, DESede | AndroidKeyStore | KeyGenerator | make a non-exportable hardware key | AES |
| RSA, EC, EdDSA, XDH, ML-*, XWING | AndroidOpenSSL | KeyPairGenerator | make a key pair | RSA, EC |
| RSA, EC, XDH, ED25519 | AndroidKeyStore | KeyPairGenerator | make a hardware key pair | RSA, EC |

## Observed usage rules

| rule | applies to |
|---|---|
| AES keys are 128, 192 or 256 bits | AndroidOpenSSL KeyGenerator |
| GCM takes a 12-byte IV via `GCMParameterSpec` | AES/GCM, AES/GCM-SIV |
| `PKCS7Padding` resolves to the `PKCS5Padding` code | AndroidOpenSSL ciphers |
| 512-bit keys are rejected | AndroidOpenSSL |
