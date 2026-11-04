# Screening list

- source: `src/perfrepair/catalog/screening.yaml`.
- a name in no row is `unknown`.
- statuses: [screening.md](screening.md).

## Counts

| Engine type | deprecated | accepted |
|---|---|---|
| MessageDigest | 3 | 10 |
| Mac | 3 | 12 |
| Signature | 10 | 54 |
| Cipher | 35 | 17 |
| KeyGenerator | 6 | 13 |
| KeyPairGenerator | 0 | 19 |
| KeyAgreement | 0 | 5 |
| SecureRandom | 0 | 1 |

## Cipher base rules

| Name | Reason | Source |
|---|---|---|
| `DES` | FIPS 46-3 withdrawn 2005; Android names DES weak | [FIPS46](https://csrc.nist.gov/pubs/fips/46-3/final) |
| `DESede` | r2 Table 1: 3-key TDEA encryption disallowed after 2023; SP 800-67r2 withdrawn January 2024 | [R2](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-131Ar2.pdf) |
| `DESedeWrap` | r2 s7: TDEA key wrapping disallowed after 2023 | [R2](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-131Ar2.pdf) |
| `RC2` | Android security lint VULNERABLE_BLOCK_CIPHER_ALGORITHMS | [LINT](https://github.com/google/android-security-lints/blob/main/checks/src/main/java/com/example/lint/checks/BadCryptographyUsageDetector.kt) |
| `ARCFOUR` | keystream biases; RFC 7465 MUST NOT in TLS; Android names RC4 weak | [RFC7465](https://www.rfc-editor.org/rfc/rfc7465) |
| `Blowfish` | 64-bit block, birthday-bound at ~32 GB independent of key length | [SWEET32](https://sweet32.info/) |

## Cipher mode rules

| Name | Reason | Source |
|---|---|---|
| `ECB` | ECB leaks plaintext structure; r3 draft disallows ECB for confidentiality; Android lint GetInstance flags ECB | [LINTGI](https://googlesamples.github.io/android-custom-lint-rules/checks/GetInstance.md.html) |

## MessageDigest deprecated

| Name | Reason | Source |
|---|---|---|
| `MD2` | preimage/collision attacks; RFC 1319 moved to Historic | [RFC6149](https://www.rfc-editor.org/rfc/rfc6149) |
| `MD5` | no collision resistance (RFC 6151 s2); Android names MD5 weak | [RFC6151](https://www.rfc-editor.org/rfc/rfc6151) |
| `SHA-1` | collision resistance below design (RFC 6194 s4); Android names SHA1 weak; NIST acceptable only where collisions don't matter | [ARISK](https://developer.android.com/privacy-and-security/risks/broken-cryptographic-algorithm) |

## Mac deprecated

| Name | Reason | Source |
|---|---|---|
| `HmacMD5` | not practically broken as MAC but RFC 6151 s2: new designs should not use it; never a target | [RFC6151](https://www.rfc-editor.org/rfc/rfc6151) |
| `SslMacMD5` | SSL 3.0 MAC (JDK SslMacCore); RFC 7568: SSLv3 MUST NOT be used | [RFC7568](https://www.rfc-editor.org/rfc/rfc7568) |
| `SslMacSHA1` | SSL 3.0 MAC (JDK SslMacCore); RFC 7568: SSLv3 MUST NOT be used | [RFC7568](https://www.rfc-editor.org/rfc/rfc7568) |

## Signature deprecated

| Name | Reason | Source |
|---|---|---|
| `MD2withRSA` | MD5/MD2 must not be used for signatures (RFC 6151 s2, RFC 6149 s6) | [RFC6151](https://www.rfc-editor.org/rfc/rfc6151) |
| `MD5withRSA` | MD5/MD2 must not be used for signatures (RFC 6151 s2, RFC 6149 s6) | [RFC6151](https://www.rfc-editor.org/rfc/rfc6151) |
| `MD5andSHA1withRSA` | TLS<=1.1 MD5\|\|SHA-1 signature; MD5 not acceptable for signatures | [RFC6151](https://www.rfc-editor.org/rfc/rfc6151) |
| `SHA1withRSA` | r2 Table 8: SHA-1 signature generation disallowed (verification legacy-only) | [R2](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-131Ar2.pdf) |
| `SHA1withECDSA` | r2 Table 8: SHA-1 signature generation disallowed (verification legacy-only) | [R2](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-131Ar2.pdf) |
| `SHA1withDSA` | r2 Table 8: SHA-1 signature generation disallowed (verification legacy-only) | [R2](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-131Ar2.pdf) |
| `SHA1withRSA/PSS` | r2 Table 8: SHA-1 signature generation disallowed (verification legacy-only) | [R2](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-131Ar2.pdf) |
| `SHA1withDSAinP1363Format` | r2 Table 8: SHA-1 signature generation disallowed (verification legacy-only) | [R2](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-131Ar2.pdf) |
| `SHA1withECDSAinP1363Format` | r2 Table 8: SHA-1 signature generation disallowed (verification legacy-only) | [R2](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-131Ar2.pdf) |
| `NONEwithDSA` | FIPS 186-5 no longer approves DSA for signature generation; verification of old signatures only | [FIPS186](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.186-5.pdf) |

## Cipher deprecated

| Name | Reason | Source |
|---|---|---|
| `DES` | FIPS 46-3 withdrawn 2005; Android names DES weak | [FIPS46](https://csrc.nist.gov/pubs/fips/46-3/final) |
| `DESede` | r2 Table 1: 3-key TDEA encryption disallowed after 2023; SP 800-67r2 withdrawn January 2024 | [R2](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-131Ar2.pdf) |
| `DESede/CBC/NoPadding` | r2 Table 1: 3-key TDEA encryption disallowed after 2023; SP 800-67r2 withdrawn January 2024 | [R2](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-131Ar2.pdf) |
| `DESede/CBC/PKCS5Padding` | r2 Table 1: 3-key TDEA encryption disallowed after 2023; SP 800-67r2 withdrawn January 2024 | [R2](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-131Ar2.pdf) |
| `DESedeWrap` | r2 s7: TDEA key wrapping disallowed after 2023 | [R2](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-131Ar2.pdf) |
| `ARCFOUR` | keystream biases; RFC 7465 MUST NOT in TLS; Android names RC4 weak | [RFC7465](https://www.rfc-editor.org/rfc/rfc7465) |
| `Blowfish` | 64-bit block, birthday-bound at ~32 GB independent of key length | [SWEET32](https://sweet32.info/) |
| `RC2` | Android security lint VULNERABLE_BLOCK_CIPHER_ALGORITHMS | [LINT](https://github.com/google/android-security-lints/blob/main/checks/src/main/java/com/example/lint/checks/BadCryptographyUsageDetector.kt) |
| `AES` | bare name: SunJCE and Android default to ECB/PKCS5Padding | [ORACLE](https://docs.oracle.com/en/java/javase/17/security/oracle-providers.html) |
| `AES/ECB/NoPadding` | ECB leaks plaintext structure; r3 draft disallows ECB for confidentiality; Android lint GetInstance flags ECB | [LINTGI](https://googlesamples.github.io/android-custom-lint-rules/checks/GetInstance.md.html) |
| `AES/ECB/PKCS5Padding` | ECB leaks plaintext structure; r3 draft disallows ECB for confidentiality; Android lint GetInstance flags ECB | [LINTGI](https://googlesamples.github.io/android-custom-lint-rules/checks/GetInstance.md.html) |
| `RSA` | no padding named: SunJCE means PKCS#1 v1.5 (r2 Table 5 disallowed after 2023), BC means no padding | [R2](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-131Ar2.pdf) |
| `RSA/ECB/PKCS1Padding` | r2 Table 5: PKCS1-v1_5 key transport disallowed after 2023; RFC 8017 Bleichenbacher | [R2](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-131Ar2.pdf) |
| `RSA/ECB/NoPadding` | textbook RSA: CWE-780 RSA without OAEP; the Android risk page links it | [CWE780](https://cwe.mitre.org/data/definitions/780.html) |
| `PBEWithMD5AndDES` | underlying DES/TDEA deprecated | [R2](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-131Ar2.pdf) |
| `PBEWithSHA1AndDES` | underlying DES/TDEA deprecated | [R2](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-131Ar2.pdf) |
| `PBEWithMD5AndTripleDES` | underlying DES/TDEA deprecated | [R2](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-131Ar2.pdf) |
| `PBEWithSHA1AndDESede` | underlying DES/TDEA deprecated | [R2](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-131Ar2.pdf) |
| `PBEWITHSHAAND2-KEYTRIPLEDES-CBC` | underlying DES/TDEA deprecated | [R2](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-131Ar2.pdf) |
| `PBEWithMD5AndRC2` | underlying RC2 flagged by Android lint | [LINT](https://github.com/google/android-security-lints/blob/main/checks/src/main/java/com/example/lint/checks/BadCryptographyUsageDetector.kt) |
| `PBEWithSHA1AndRC2` | underlying RC2 flagged by Android lint | [LINT](https://github.com/google/android-security-lints/blob/main/checks/src/main/java/com/example/lint/checks/BadCryptographyUsageDetector.kt) |
| `PBEWithSHA1AndRC2_128` | underlying RC2 flagged by Android lint | [LINT](https://github.com/google/android-security-lints/blob/main/checks/src/main/java/com/example/lint/checks/BadCryptographyUsageDetector.kt) |
| `PBEWithSHA1AndRC2_40` | underlying RC2 flagged by Android lint | [LINT](https://github.com/google/android-security-lints/blob/main/checks/src/main/java/com/example/lint/checks/BadCryptographyUsageDetector.kt) |
| `PBEWithSHA1AndRC4_128` | underlying RC4 | [RFC7465](https://www.rfc-editor.org/rfc/rfc7465) |
| `PBEWithSHA1AndRC4_40` | underlying RC4 | [RFC7465](https://www.rfc-editor.org/rfc/rfc7465) |
| `PBEWITHSHAAND128BITAES-CBC-BC` | BC binds it to the PKCS12 KDF; RFC 7292 App B: not recommended, deprecated for new usage | [RFC7292](https://www.rfc-editor.org/rfc/rfc7292) |
| `PBEWITHSHAAND192BITAES-CBC-BC` | BC binds it to the PKCS12 KDF; RFC 7292 App B: not recommended, deprecated for new usage | [RFC7292](https://www.rfc-editor.org/rfc/rfc7292) |
| `PBEWITHSHAAND256BITAES-CBC-BC` | BC binds it to the PKCS12 KDF; RFC 7292 App B: not recommended, deprecated for new usage | [RFC7292](https://www.rfc-editor.org/rfc/rfc7292) |
| `PBEWITHSHA256AND128BITAES-CBC-BC` | BC binds it to the PKCS12 KDF; RFC 7292 App B: not recommended, deprecated for new usage | [RFC7292](https://www.rfc-editor.org/rfc/rfc7292) |
| `PBEWITHSHA256AND192BITAES-CBC-BC` | BC binds it to the PKCS12 KDF; RFC 7292 App B: not recommended, deprecated for new usage | [RFC7292](https://www.rfc-editor.org/rfc/rfc7292) |
| `PBEWITHSHA256AND256BITAES-CBC-BC` | BC binds it to the PKCS12 KDF; RFC 7292 App B: not recommended, deprecated for new usage | [RFC7292](https://www.rfc-editor.org/rfc/rfc7292) |
| `PBEWITHSHAANDTWOFISH-CBC` | BC binds it to the PKCS12 KDF; RFC 7292 App B: not recommended, deprecated for new usage | [RFC7292](https://www.rfc-editor.org/rfc/rfc7292) |
| `PBEWITHMD5AND128BITAES-CBC-OPENSSL` | BC OpenSSL KDF: PKCS 5 scheme 1 with MD5, iteration count 1; RFC 8018 s5.1 PBKDF1 not recommended for new applications | [RFC8018](https://www.rfc-editor.org/rfc/rfc8018) |
| `PBEWITHMD5AND192BITAES-CBC-OPENSSL` | BC OpenSSL KDF: PKCS 5 scheme 1 with MD5, iteration count 1; RFC 8018 s5.1 PBKDF1 not recommended for new applications | [RFC8018](https://www.rfc-editor.org/rfc/rfc8018) |
| `PBEWITHMD5AND256BITAES-CBC-OPENSSL` | BC OpenSSL KDF: PKCS 5 scheme 1 with MD5, iteration count 1; RFC 8018 s5.1 PBKDF1 not recommended for new applications | [RFC8018](https://www.rfc-editor.org/rfc/rfc8018) |

## KeyGenerator deprecated

| Name | Reason | Source |
|---|---|---|
| `HmacMD5` | keys a deprecated MAC | [RFC6151](https://www.rfc-editor.org/rfc/rfc6151) |
| `ARCFOUR` | keys RC4 | [RFC7465](https://www.rfc-editor.org/rfc/rfc7465) |
| `DES` | keys DES | [FIPS46](https://csrc.nist.gov/pubs/fips/46-3/final) |
| `DESede` | keys TDEA | [R2](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-131Ar2.pdf) |
| `Blowfish` | keys a 64-bit block cipher | [SWEET32](https://sweet32.info/) |
| `RC2` | keys RC2 | [LINT](https://github.com/google/android-security-lints/blob/main/checks/src/main/java/com/example/lint/checks/BadCryptographyUsageDetector.kt) |
