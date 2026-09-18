# tree

Level 1 engine type, level 2 algorithm, level 3 modes, paddings, providers.
Mode and padding names are defined by the Java Security Standard Algorithm Names specification.
Measured on Eclipse Adoptium 25.0.3, not an Android device (#14).

## specification

- modes: NONE, CBC, CCM, CFB, CFBx, CTR, CTS, ECB, GCM, KW, KWP, OFB, OFBx, PCBC
- paddings: NoPadding, ISO10126Padding, OAEPPadding, OAEPWith<digest>And<mgf>Padding, PKCS1Padding, PKCS5Padding, SSL3Padding

## Cipher

### AES

- modes: ECB, CBC, PCBC, CTR, CTS, CFB, OFB, CFB8, CFB16, CFB24, CFB32, CFB40, CFB48, CFB56, CFB64, OFB8, OFB16, OFB24, OFB32, OFB40, OFB48, OFB56, OFB64, CFB72, CFB80, CFB88, CFB96, CFB104, CFB112, CFB120, CFB128, OFB72, OFB80, OFB88, OFB96, OFB104, OFB112, OFB120, OFB128
- paddings: NOPADDING, PKCS5PADDING, ISO10126PADDING
- providers: SunJCE

### AES/GCM/NoPadding

- modes: GCM
- providers: SunJCE

### AES/KW/NoPadding

- providers: SunJCE

### AES/KW/PKCS5Padding

- providers: SunJCE

### AES/KWP/NoPadding

- providers: SunJCE

### AES_128/CBC/NoPadding

- providers: SunJCE

### AES_128/CFB/NoPadding

- providers: SunJCE

### AES_128/ECB/NoPadding

- providers: SunJCE

### AES_128/GCM/NoPadding

- modes: GCM
- providers: SunJCE

### AES_128/KW/NoPadding

- providers: SunJCE

### AES_128/KW/PKCS5Padding

- providers: SunJCE

### AES_128/KWP/NoPadding

- providers: SunJCE

### AES_128/OFB/NoPadding

- providers: SunJCE

### AES_192/CBC/NoPadding

- providers: SunJCE

### AES_192/CFB/NoPadding

- providers: SunJCE

### AES_192/ECB/NoPadding

- providers: SunJCE

### AES_192/GCM/NoPadding

- modes: GCM
- providers: SunJCE

### AES_192/KW/NoPadding

- providers: SunJCE

### AES_192/KW/PKCS5Padding

- providers: SunJCE

### AES_192/KWP/NoPadding

- providers: SunJCE

### AES_192/OFB/NoPadding

- providers: SunJCE

### AES_256/CBC/NoPadding

- providers: SunJCE

### AES_256/CFB/NoPadding

- providers: SunJCE

### AES_256/ECB/NoPadding

- providers: SunJCE

### AES_256/GCM/NoPadding

- modes: GCM
- providers: SunJCE

### AES_256/KW/NoPadding

- providers: SunJCE

### AES_256/KW/PKCS5Padding

- providers: SunJCE

### AES_256/KWP/NoPadding

- providers: SunJCE

### AES_256/OFB/NoPadding

- providers: SunJCE

### ARCFOUR

- modes: ECB
- paddings: NOPADDING
- providers: SunJCE

### Blowfish

- modes: ECB, CBC, PCBC, CTR, CTS, CFB, OFB, CFB8, CFB16, CFB24, CFB32, CFB40, CFB48, CFB56, CFB64, OFB8, OFB16, OFB24, OFB32, OFB40, OFB48, OFB56, OFB64
- paddings: NOPADDING, PKCS5PADDING, ISO10126PADDING
- providers: SunJCE

### ChaCha20

- providers: SunJCE

### ChaCha20-Poly1305

- providers: SunJCE

### DES

- modes: ECB, CBC, PCBC, CTR, CTS, CFB, OFB, CFB8, CFB16, CFB24, CFB32, CFB40, CFB48, CFB56, CFB64, OFB8, OFB16, OFB24, OFB32, OFB40, OFB48, OFB56, OFB64
- paddings: NOPADDING, PKCS5PADDING, ISO10126PADDING
- providers: SunJCE

### DESede

- modes: ECB, CBC, PCBC, CTR, CTS, CFB, OFB, CFB8, CFB16, CFB24, CFB32, CFB40, CFB48, CFB56, CFB64, OFB8, OFB16, OFB24, OFB32, OFB40, OFB48, OFB56, OFB64
- paddings: NOPADDING, PKCS5PADDING, ISO10126PADDING
- providers: SunJCE

### DESedeWrap

- modes: CBC
- paddings: NOPADDING
- providers: SunJCE

### PBEWithHmacSHA1AndAES_128

- providers: SunJCE

### PBEWithHmacSHA1AndAES_256

- providers: SunJCE

### PBEWithHmacSHA224AndAES_128

- providers: SunJCE

### PBEWithHmacSHA224AndAES_256

- providers: SunJCE

### PBEWithHmacSHA256AndAES_128

- providers: SunJCE

### PBEWithHmacSHA256AndAES_256

- providers: SunJCE

### PBEWithHmacSHA384AndAES_128

- providers: SunJCE

### PBEWithHmacSHA384AndAES_256

- providers: SunJCE

### PBEWithHmacSHA512/224AndAES_128

- providers: SunJCE

### PBEWithHmacSHA512/224AndAES_256

- providers: SunJCE

### PBEWithHmacSHA512/256AndAES_128

- providers: SunJCE

### PBEWithHmacSHA512/256AndAES_256

- providers: SunJCE

### PBEWithHmacSHA512AndAES_128

- providers: SunJCE

### PBEWithHmacSHA512AndAES_256

- providers: SunJCE

### PBEWithMD5AndDES

- providers: SunJCE

### PBEWithMD5AndTripleDES

- providers: SunJCE

### PBEWithSHA1AndDESede

- providers: SunJCE

### PBEWithSHA1AndRC2_128

- providers: SunJCE

### PBEWithSHA1AndRC2_40

- providers: SunJCE

### PBEWithSHA1AndRC4_128

- providers: SunJCE

### PBEWithSHA1AndRC4_40

- providers: SunJCE

### RC2

- modes: ECB, CBC, PCBC, CTR, CTS, CFB, OFB, CFB8, CFB16, CFB24, CFB32, CFB40, CFB48, CFB56, CFB64, OFB8, OFB16, OFB24, OFB32, OFB40, OFB48, OFB56, OFB64
- paddings: NOPADDING, PKCS5PADDING, ISO10126PADDING
- providers: SunJCE

### RSA

- modes: ECB
- paddings: NOPADDING, PKCS1PADDING, OAEPPADDING, OAEPWITHMD5ANDMGF1PADDING, OAEPWITHSHA1ANDMGF1PADDING, OAEPWITHSHA-1ANDMGF1PADDING, OAEPWITHSHA-224ANDMGF1PADDING, OAEPWITHSHA-256ANDMGF1PADDING, OAEPWITHSHA-384ANDMGF1PADDING, OAEPWITHSHA-512ANDMGF1PADDING, OAEPWITHSHA-512/224ANDMGF1PADDING, OAEPWITHSHA-512/256ANDMGF1PADDING
- providers: SunJCE

## KeyAgreement

### DiffieHellman

- providers: SunJCE

### ECDH

- providers: SunEC

### X25519

- providers: SunEC

### X448

- providers: SunEC

### XDH

- providers: SunEC

## KeyGenerator

### AES

- providers: SunJCE

### ARCFOUR

- providers: SunJCE

### Blowfish

- providers: SunJCE

### ChaCha20

- providers: SunJCE

### DES

- providers: SunJCE

### DESede

- providers: SunJCE

### HmacMD5

- providers: SunJCE

### HmacSHA1

- providers: SunJCE

### HmacSHA224

- providers: SunJCE

### HmacSHA256

- providers: SunJCE

### HmacSHA3-224

- providers: SunJCE

### HmacSHA3-256

- providers: SunJCE

### HmacSHA3-384

- providers: SunJCE

### HmacSHA3-512

- providers: SunJCE

### HmacSHA384

- providers: SunJCE

### HmacSHA512

- providers: SunJCE

### HmacSHA512/224

- providers: SunJCE

### HmacSHA512/256

- providers: SunJCE

### RC2

- providers: SunJCE

### SunTls12Prf

- providers: SunJCE

### SunTlsKeyMaterial

- providers: SunJCE

### SunTlsMasterSecret

- providers: SunJCE

### SunTlsPrf

- providers: SunJCE

### SunTlsRsaPremasterSecret

- providers: SunJCE

## KeyPairGenerator

### DSA

- providers: SUN

### DiffieHellman

- providers: SunJCE

### EC

- providers: SunEC

### Ed25519

- providers: SunEC

### Ed448

- providers: SunEC

### EdDSA

- providers: SunEC

### ML-DSA

- providers: SUN

### ML-DSA-44

- providers: SUN

### ML-DSA-65

- providers: SUN

### ML-DSA-87

- providers: SUN

### ML-KEM

- providers: SunJCE

### ML-KEM-1024

- providers: SunJCE

### ML-KEM-512

- providers: SunJCE

### ML-KEM-768

- providers: SunJCE

### RSA

- providers: SunRsaSign

### RSASSA-PSS

- providers: SunRsaSign

### X25519

- providers: SunEC

### X448

- providers: SunEC

### XDH

- providers: SunEC

## Mac

### HmacMD5

- providers: SunJCE

### HmacPBESHA1

- providers: SunJCE

### HmacPBESHA224

- providers: SunJCE

### HmacPBESHA256

- providers: SunJCE

### HmacPBESHA384

- providers: SunJCE

### HmacPBESHA512

- providers: SunJCE

### HmacPBESHA512/224

- providers: SunJCE

### HmacPBESHA512/256

- providers: SunJCE

### HmacSHA1

- providers: SunJCE

### HmacSHA224

- providers: SunJCE

### HmacSHA256

- providers: SunJCE

### HmacSHA3-224

- providers: SunJCE

### HmacSHA3-256

- providers: SunJCE

### HmacSHA3-384

- providers: SunJCE

### HmacSHA3-512

- providers: SunJCE

### HmacSHA384

- providers: SunJCE

### HmacSHA512

- providers: SunJCE

### HmacSHA512/224

- providers: SunJCE

### HmacSHA512/256

- providers: SunJCE

### PBEWithHmacSHA1

- providers: SunJCE

### PBEWithHmacSHA224

- providers: SunJCE

### PBEWithHmacSHA256

- providers: SunJCE

### PBEWithHmacSHA384

- providers: SunJCE

### PBEWithHmacSHA512

- providers: SunJCE

### PBEWithHmacSHA512/224

- providers: SunJCE

### PBEWithHmacSHA512/256

- providers: SunJCE

### SslMacMD5

- providers: SunJCE

### SslMacSHA1

- providers: SunJCE

## MessageDigest

### MD2

- providers: SUN

### MD5

- providers: SUN

### SHA-1

- providers: SUN

### SHA-224

- providers: SUN

### SHA-256

- providers: SUN

### SHA-384

- providers: SUN

### SHA-512

- providers: SUN

### SHA-512/224

- providers: SUN

### SHA-512/256

- providers: SUN

### SHA3-224

- providers: SUN

### SHA3-256

- providers: SUN

### SHA3-384

- providers: SUN

### SHA3-512

- providers: SUN

### SHAKE128-256

- providers: SUN

### SHAKE256-512

- providers: SUN

## Signature

### Ed25519

- providers: SunEC

### Ed448

- providers: SunEC

### EdDSA

- providers: SunEC

### HSS/LMS

- providers: SUN

### MD2withRSA

- providers: SunRsaSign

### MD5andSHA1withRSA

- providers: SunJSSE

### MD5withRSA

- providers: SunRsaSign

### ML-DSA

- providers: SUN

### ML-DSA-44

- providers: SUN

### ML-DSA-65

- providers: SUN

### ML-DSA-87

- providers: SUN

### NONEwithDSA

- providers: SUN

### NONEwithDSAinP1363Format

- providers: SUN

### NONEwithECDSA

- providers: SunEC

### NONEwithECDSAinP1363Format

- providers: SunEC

### NONEwithRSA

- providers: SunJCE

### RSASSA-PSS

- providers: SunRsaSign

### SHA1withDSA

- providers: SUN

### SHA1withDSAinP1363Format

- providers: SUN

### SHA1withECDSA

- providers: SunEC

### SHA1withECDSAinP1363Format

- providers: SunEC

### SHA1withRSA

- providers: SunRsaSign

### SHA224withDSA

- providers: SUN

### SHA224withDSAinP1363Format

- providers: SUN

### SHA224withECDSA

- providers: SunEC

### SHA224withECDSAinP1363Format

- providers: SunEC

### SHA224withRSA

- providers: SunRsaSign

### SHA256withDSA

- providers: SUN

### SHA256withDSAinP1363Format

- providers: SUN

### SHA256withECDSA

- providers: SunEC

### SHA256withECDSAinP1363Format

- providers: SunEC

### SHA256withRSA

- providers: SunRsaSign

### SHA3-224withDSA

- providers: SUN

### SHA3-224withDSAinP1363Format

- providers: SUN

### SHA3-224withECDSA

- providers: SunEC

### SHA3-224withECDSAinP1363Format

- providers: SunEC

### SHA3-224withRSA

- providers: SunRsaSign

### SHA3-256withDSA

- providers: SUN

### SHA3-256withDSAinP1363Format

- providers: SUN

### SHA3-256withECDSA

- providers: SunEC

### SHA3-256withECDSAinP1363Format

- providers: SunEC

### SHA3-256withRSA

- providers: SunRsaSign

### SHA3-384withDSA

- providers: SUN

### SHA3-384withDSAinP1363Format

- providers: SUN

### SHA3-384withECDSA

- providers: SunEC

### SHA3-384withECDSAinP1363Format

- providers: SunEC

### SHA3-384withRSA

- providers: SunRsaSign

### SHA3-512withDSA

- providers: SUN

### SHA3-512withDSAinP1363Format

- providers: SUN

### SHA3-512withECDSA

- providers: SunEC

### SHA3-512withECDSAinP1363Format

- providers: SunEC

### SHA3-512withRSA

- providers: SunRsaSign

### SHA384withDSA

- providers: SUN

### SHA384withDSAinP1363Format

- providers: SUN

### SHA384withECDSA

- providers: SunEC

### SHA384withECDSAinP1363Format

- providers: SunEC

### SHA384withRSA

- providers: SunRsaSign

### SHA512/224withRSA

- providers: SunRsaSign

### SHA512/256withRSA

- providers: SunRsaSign

### SHA512withDSA

- providers: SUN

### SHA512withDSAinP1363Format

- providers: SUN

### SHA512withECDSA

- providers: SunEC

### SHA512withECDSAinP1363Format

- providers: SunEC

### SHA512withRSA

- providers: SunRsaSign

