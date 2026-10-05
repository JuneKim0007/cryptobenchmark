| group | case | op | key | input | n | unit | mean | median | q1 | q3 | cov | qcd | headline | flag |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| symmetric-cipher | AES/GCM (AndroidOpenSSL) | ENCRYPT | 128 | 64B | 50 | MB/s | 45.97 | 49.88 | 44.61 | 51.31 | 19.9% | 7.0% | median | noisy |
| symmetric-cipher | AES/GCM (AndroidOpenSSL) | ENCRYPT | 128 | 1KiB | 50 | MB/s | 560.4 | 566.8 | 555.5 | 578 | 5.0% | 2.0% | median | noisy |
| symmetric-cipher | AES/GCM (AndroidOpenSSL) | ENCRYPT | 128 | 16KiB | 50 | MB/s | 1947 | 1995 | 1951 | 2063 | 11.2% | 2.8% | median | noisy |
| symmetric-cipher | ChaCha20 (AndroidOpenSSL) | ENCRYPT | - | 64B | 50 | MB/s | 76.58 | 79.31 | 76.85 | 80.88 | 10.8% | 2.6% | median | noisy |
| symmetric-cipher | ChaCha20 (AndroidOpenSSL) | ENCRYPT | - | 1KiB | 50 | MB/s | 705.9 | 718.6 | 706.8 | 726.1 | 5.7% | 1.3% | median | noisy |
| symmetric-cipher | ChaCha20 (AndroidOpenSSL) | ENCRYPT | - | 16KiB | 50 | MB/s | 1523 | 1561 | 1520 | 1586 | 9.1% | 2.1% | median | noisy |
| asymmetric-cipher | RSA/PKCS1Padding (AndroidOpenSSL) | ENCRYPT | 2048 | 32B | 50 | us/op | 9.266 | 9.181 | 9.119 | 9.328 | 2.5% | 1.1% | mean |  |
| asymmetric-cipher | RSA/PKCS1Padding (AndroidOpenSSL) | ENCRYPT | 4096 | 32B | 50 | us/op | 29.77 | 29.57 | 29.49 | 29.76 | 2.2% | 0.4% | mean |  |
| signature | SHA256withRSA (AndroidOpenSSL) | SIGN | 2048 | 64B | 50 | us/op | 408.3 | 404.4 | 402.4 | 407.2 | 3.4% | 0.6% | mean |  |
| signature | SHA256withRSA (AndroidOpenSSL) | SIGN | 2048 | 1KiB | 50 | us/op | 402.5 | 401.7 | 400.8 | 403.1 | 0.6% | 0.3% | mean |  |
| hash | SHA-256 (AndroidOpenSSL) | DIGEST | - | 64B | 50 | MB/s | 287.4 | 293.6 | 287 | 297.3 | 5.5% | 1.8% | median | noisy |
| hash | SHA-256 (AndroidOpenSSL) | DIGEST | - | 1KiB | 50 | MB/s | 1699 | 1981 | 1682 | 2023 | 30.3% | 9.2% | median | noisy |
| hash | SHA-256 (AndroidOpenSSL) | DIGEST | - | 16KiB | 50 | MB/s | 3102 | 3166 | 3114 | 3201 | 6.2% | 1.4% | median | noisy |
| mac | HmacSHA256 (AndroidOpenSSL) | COMPUTE_MAC | - | 64B | 50 | MB/s | 253.4 | 255 | 253 | 256 | 1.5% | 0.6% | mean |  |
| mac | HmacSHA256 (AndroidOpenSSL) | COMPUTE_MAC | - | 1KiB | 50 | MB/s | 1808 | 1825 | 1804 | 1841 | 3.1% | 1.0% | mean |  |
| mac | HmacSHA256 (AndroidOpenSSL) | COMPUTE_MAC | - | 16KiB | 50 | MB/s | 3155 | 3172 | 3130 | 3189 | 1.5% | 0.9% | mean |  |
| keygen-asymmetric | EC (AndroidOpenSSL) | GENERATE_KEY_PAIR | - | n-a | 50 | us/op | 19.54 | 19.53 | 19.44 | 19.61 | 0.8% | 0.4% | mean |  |
