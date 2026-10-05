| case | op | key | input | median ns | p90 ns | CoV | MB/s |
|---|---|---|---|---|---|---|---|
| AES/GCM/NoPadding | ENCRYPT | 128 | 64 | 1,283.0 | 1,618 | 21.4% | 50 |
| AES/GCM/NoPadding | ENCRYPT | 128 | 1024 | 1,806.5 | 1,884 | 5.0% | 567 |
| AES/GCM/NoPadding | ENCRYPT | 128 | 16384 | 8,212.5 | 9,368 | 11.4% | 1995 |
| ChaCha20 | ENCRYPT | - | 64 | 807.0 | 896 | 11.0% | 79 |
| ChaCha20 | ENCRYPT | - | 1024 | 1,425.0 | 1,496 | 5.7% | 719 |
| ChaCha20 | ENCRYPT | - | 16384 | 10,496.0 | 11,277 | 9.2% | 1561 |
| RSA/ECB/PKCS1Padding | ENCRYPT | 2048 | 32 | 9,180.5 | 9,449 | 2.5% | 3 |
| RSA/ECB/PKCS1Padding | ENCRYPT | 4096 | 32 | 29,568.5 | 29,961 | 2.2% | 1 |
| EC | GENERATE_KEY_PAIR | - | - | 19,534.5 | 19,745 | 0.8% | - |
| HmacSHA256 | COMPUTE_MAC | - | 64 | 251.0 | 257 | 1.5% | 255 |
| HmacSHA256 | COMPUTE_MAC | - | 1024 | 561.0 | 585 | 3.1% | 1825 |
| HmacSHA256 | COMPUTE_MAC | - | 16384 | 5,165.0 | 5,296 | 1.5% | 3172 |
| SHA-256 | DIGEST | - | 64 | 218.0 | 234 | 5.6% | 294 |
| SHA-256 | DIGEST | - | 1024 | 517.0 | 808 | 34.9% | 1981 |
| SHA-256 | DIGEST | - | 16384 | 5,174.5 | 5,550 | 6.3% | 3166 |
| SHA256withRSA | SIGN | 2048 | 64 | 404,375.0 | 413,766 | 3.4% | 0 |
| SHA256withRSA | SIGN | 2048 | 1024 | 401,675.0 | 405,381 | 0.6% | 3 |
