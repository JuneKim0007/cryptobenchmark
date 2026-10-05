| group | case | op | key | input | n | mean | sd (ns) | cov | median | q1 | q3 | qcd | headline | unit | flag |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| symmetric-cipher | AES/GCM (AndroidOpenSSL) | ENCRYPT | 128 | 64B | 50 | 45.97 | 277.7 | 19.9% | 49.88 | 44.61 | 51.31 | 7.0% | median | MB/s | noisy |
| symmetric-cipher | AES/GCM (AndroidOpenSSL) | ENCRYPT | 128 | 1KiB | 50 | 560.4 | 91.51 | 5.0% | 566.8 | 555.5 | 578 | 2.0% | median | MB/s | noisy |
| symmetric-cipher | AES/GCM (AndroidOpenSSL) | ENCRYPT | 128 | 16KiB | 50 | 1947 | 946.1 | 11.2% | 1995 | 1951 | 2063 | 2.8% | median | MB/s | noisy |
| symmetric-cipher | ChaCha20 (AndroidOpenSSL) | ENCRYPT | - | 64B | 50 | 76.58 | 89.97 | 10.8% | 79.31 | 76.85 | 80.88 | 2.6% | median | MB/s | noisy |
| symmetric-cipher | ChaCha20 (AndroidOpenSSL) | ENCRYPT | - | 1KiB | 50 | 705.9 | 82.16 | 5.7% | 718.6 | 706.8 | 726.1 | 1.3% | median | MB/s | noisy |
| symmetric-cipher | ChaCha20 (AndroidOpenSSL) | ENCRYPT | - | 16KiB | 50 | 1523 | 978 | 9.1% | 1561 | 1520 | 1586 | 2.1% | median | MB/s | noisy |
| asymmetric-cipher | RSA/PKCS1Padding (AndroidOpenSSL) | ENCRYPT | 2048 | 32B | 50 | 9.266 | 232.3 | 2.5% | 9.181 | 9.119 | 9.328 | 1.1% | mean | us/op |  |
| asymmetric-cipher | RSA/PKCS1Padding (AndroidOpenSSL) | ENCRYPT | 4096 | 32B | 50 | 29.77 | 644.1 | 2.2% | 29.57 | 29.49 | 29.76 | 0.4% | mean | us/op |  |
| signature | SHA256withRSA (AndroidOpenSSL) | SIGN | 2048 | 64B | 50 | 408.3 | 1.399e+04 | 3.4% | 404.4 | 402.4 | 407.2 | 0.6% | mean | us/op |  |
| signature | SHA256withRSA (AndroidOpenSSL) | SIGN | 2048 | 1KiB | 50 | 402.5 | 2576 | 0.6% | 401.7 | 400.8 | 403.1 | 0.3% | mean | us/op |  |
| hash | SHA-256 (AndroidOpenSSL) | DIGEST | - | 64B | 50 | 287.4 | 12.35 | 5.5% | 293.6 | 287 | 297.3 | 1.8% | median | MB/s | noisy |
| hash | SHA-256 (AndroidOpenSSL) | DIGEST | - | 1KiB | 50 | 1699 | 182.4 | 30.3% | 1981 | 1682 | 2023 | 9.2% | median | MB/s | noisy |
| hash | SHA-256 (AndroidOpenSSL) | DIGEST | - | 16KiB | 50 | 3102 | 329.5 | 6.2% | 3166 | 3114 | 3201 | 1.4% | median | MB/s | noisy |
| mac | HmacSHA256 (AndroidOpenSSL) | COMPUTE_MAC | - | 64B | 50 | 253.4 | 3.677 | 1.5% | 255 | 253 | 256 | 0.6% | mean | MB/s |  |
| mac | HmacSHA256 (AndroidOpenSSL) | COMPUTE_MAC | - | 1KiB | 50 | 1808 | 17.75 | 3.1% | 1825 | 1804 | 1841 | 1.0% | mean | MB/s |  |
| mac | HmacSHA256 (AndroidOpenSSL) | COMPUTE_MAC | - | 16KiB | 50 | 3155 | 80.07 | 1.5% | 3172 | 3130 | 3189 | 0.9% | mean | MB/s |  |
| keygen-asymmetric | EC (AndroidOpenSSL) | GENERATE_KEY_PAIR | - | n-a | 50 | 19.54 | 152.5 | 0.8% | 19.53 | 19.44 | 19.61 | 0.4% | mean | us/op |  |
