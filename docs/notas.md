

### RSA

in RSA encryption, the plaintext input size is subject to certain restrictions and can have an impact on processing requirements. Here are some considerations:
1. Input Size Limit:
    * The size of the plaintext that can be directly encrypted using RSA is limited by the size of the RSA key used.
    * RSA operates on fixed-size blocks of data, and the maximum plaintext size that can be directly encrypted depends on the key size minus padding overhead.
    * For example, with a 2048-bit RSA key and using the commonly used PKCS#1 v1.5 padding scheme, the maximum plaintext size is typically 245 bytes.

### AndroidKeyStoreBCWorkaround

The purpose of the AndroidKeyStoreBCWorkaround provider is to enable the use of Bouncy Castle cryptographic algorithms in conjunction with the Android Keystore system on older Android versions. Prior to Android 6.0, the Android Keystore system had limitations in terms of supported cryptographic algorithms. It primarily supported the default algorithms provided by the platform, and Bouncy Castle algorithms were not directly accessible.
The AndroidKeyStoreBCWorkaround provider bridges this gap by acting as an intermediary. It wraps the Bouncy Castle algorithms and allows them to be used through the Android Keystore system. This enables developers to leverage Bouncy Castle cryptographic algorithms while benefiting from the secure storage and hardware-backed protection provided by the Android Keystore.

### HMAC
segundo o rfc do hmac,   /* if key is longer than 64 bytes reset it to key=MD5(key) o que me leva a querer que a chave nunca chega a ser maior que o tamanho do bloco?
If the key size exceeds the block size, the HMAC implementation typically applies additional processing to handle the longer key. However, this does not enhance the security of the HMAC construction. In fact, it may introduce unnecessary computational overhead without any practical benefit.
The recommended approach for selecting the key size in HMAC is to align it with the security strength requirements of the hash function and the desired level of security for the application. For most cryptographic applications, a key size of 128 bits or higher is considered secure. Using a key size significantly larger than the block size does not provide any additional security advantages and can lead to unnecessary complexity and performance implications.

### Stream vs bock ciphers

1. Speed: In general, stream ciphers tend to be faster than block ciphers. Stream ciphers encrypt and decrypt data bit by bit or byte by byte, allowing for efficient processing of large volumes of data in real-time. Block ciphers, on the other hand, typically operate on fixed-size blocks of data, which may require additional padding or mode of operation for handling data that is not a perfect multiple of the block size.
2. Resource Usage: Stream ciphers often require fewer computational resources and memory compared to block ciphers. Stream ciphers are designed to process data stream by stream without the need for maintaining state between different blocks of data. Block ciphers may require more memory and processing power to handle the block-by-block encryption and decryption operations.
3. Security and Complexity: Both block ciphers and stream ciphers can provide strong security if implemented correctly. The security of a cipher depends on factors such as the key size, the algorithm's design, and the quality of its implementation. While both types of ciphers have their own security considerations, block ciphers are generally more widely studied and analyzed due to their long history of use, which may provide some assurance regarding their security.

### Notas soltas

-  block size refers to the internal processing unit of the hash function. Block sizes:
    - MD5 (Message Digest Algorithm 5): The block size is 512 bits (64 bytes).
    - SHA-1 (Secure Hash Algorithm 1): The block size is 512 bits (64 bytes).
    - SHA-224 (Secure Hash Algorithm 224-bit): The block size is 512 bits (64 bytes).
    - SHA-256 (Secure Hash Algorithm 256-bit): The block size is 512 bits (64 bytes).
    - SHA-384 (Secure Hash Algorithm384-bit): The block size is 1024 bits (128 bytes)
    - SHA-512 (Secure Hash Algorithm 512-bit): The block size is 1024 bits (128 bytes)
- Chacha20 é uma única stream cipher das simétricas?
- Block ciphers: A block cipher processes the data blocks of fixed size. Usually, the size of a message is larger than the block size. Hence, the long message is divided into a series of sequential message blocks, and the cipher operates on these blocks one at a time.
- Stream ciphers: one binary digit at time
- Wikipedia: SHA-3  (family) has been criticized for being slow on instruction set architectures (CPUs) which do not have instructions meant specially for computing Keccak functions faster – SHA2-512 is more than twice as fast as SHA3-512, and SHA-1 is more than three times as fast on an Intel Skylake processor clocked at 3.2 GHz.[40] 
- Paper Crypto misuses 2016 - Due to that ECB is the default encryption mode set by Android, the developer also uses ECB mode if they only define “AES” in their code. -> isto ainda acontece !!!
- [11] found that about 90% of the 12,000 applications in the Google Play marketplace that use cryptographic APIs make at least one mistake.
- Shuai et al. [29] built a collection of cryptography misuse models, and implemented an automatic misuse detection tool, Crypto Misuse Analyzer (CMA). hey found that more than half of the apps they examined su↵er from cryptographic misuses.
- No pixel 3a, usar chaves >= 2048 com DSA da java.security.InvalidKeyException: Key is too strong for this signature algorithm
- Nao da para gerar chaves ecdsa e ec sem instalar outro provider (spongycastle ou outra versão do bouncycastle)
- Arc4 bc no redmi levanta error msg no log por ser deprecated no futuro
- Chacha20  ->  Key size must be 256 bits
- adb shell am instrument -w -r -e log true -e package 'com.example.cryptobenchmark' com.example.cryptobenchmark.test/android.support.test.runner.AndroidJUnitRunner 
- Potencial tip: mudar para sha256 sse quant nao é problema
- Nao posso cifrar com curvas elípticas pk apesar de haver 3 providers a dizer 
- Justificar que so se usaram primitivas presentes nos dispositivos
- https://www.openssl.org/docs/man3.0/man1/openssl-speed.html
- Como correr benchmark?
- Garantias  para certificar de que os benchmarks sao justos:
    - Setup, cool down time
    - Mesmo input (usar tamanhos do openssl )
    - Mesmo tamanhos de chaves
- Rsa pode ser usado para assinaturas. Rsa é block cipher, dsa é stream cipher. The Dsa is a faster signature, but RSA is more efficient at verification.
The original DSS constrained L (key length) to be a multiple of 64 between 512 and 1024 inclusive. NIST 800-57 recommends lengths of 2048 (or 3072) for keys with security lifetimes extending beyond 2010 (or 2030).
* Rsa vs dsa
* Faster at encrypting: RSA
* Faster at decrypting: DSA
* Faster at generating a digital signature or "signing": DSA
* Faster at verifying a digital signature: RSA
Another thing to consider is that DSA-generated signatures are significantly smaller. Thus, if you've got limited bandwidth, you might want to use DSA.
- DSA
    * Highly Robust: DSA is highly robust in the security and stability aspect compared to alternative signature verification algorithms.
    * Better Speed: The key generation is much faster compared to the RSA algorithm and such.
    * Less Storage: DSA requires less storage space to work its entire cycle.
    * Patent Free: When NIST released it, it was patent-free to enable its global use free of cost.
1. Limited Key Length: DSA has limited key lengths, which limit its use in specific applications.
2. Rigid Key Management: Key management is rigid and requires specific key lengths.
3. Limited Digital Certificate Support: DSA does not support certificates, which limits its use in specific applications.
4. Incremental signature algorithm: DSA is not an incremental signature algorithm, meaning it cannot be updated or changed once a signature is generated.
5. Relatively new: DSA is a relatively new algorithm and has not been extensively studied or vetted like some of the more established algorithms.
6. Impact on storage and transmission: DSA signatures can be larger than signatures created with other algorithms, which can impact storage and transmission efficiency.


Redmi 8:
- Nao consigo meter os rsa - OAEPWITHSHA-XANDMGF1PADDING a correr com o keystore. Para ja, na verdade o keystore so suporta o sha1, apesar de o getServices do Provider do Java.Security dizer que o provider suporta estes algoritmos. Apos N tentativas de meter a correr,  consigo cifrar mas nao consigo decifrar pk da um erro de keystore. A cifragem aparentemente funciona…  
- Rsa/ecb/nopad
- SHA384WITHRSA/PSS
- Sha’s with RSA
- RSA/ECB/OAEPPADDING
- AES/CBC/PKCS7PADDING -> {ConfigurableCryptoPrimitive@16515} 
- RSA/ECB/PKCS1PADDING -> {ConfigurableCryptoPrimitive@16513} 
Notas:
- Sha256 vs outras: the only real advantage that SHA-512 might have over SHA-256 is collision resistance, a term that in cryptography has a very narrow meaning. SHA-256 claims 128-bit collision resistance, SHA-512 claims 256-bit. If or when a practical quantum computer is built, we might need the 256-bit collision resistance.
Since SSL certificates typically have expiration dates in a relatively short term, it's just fine to get a SHA-256 certificate today, because it'll expire before a practical quantum computer is built (if that ever happens).
Apart from that:
* SHA-256 outputs are shorter, which saves bandwidth.
* Different hardware favors different functions. SHA-512 is generally faster on 64-bit processors, SHA-256 faster on 32-bit processors. (Try the command openssl speed sha256 sha512 on your computer.)
* SHA-512/256 sits right in between the two functions—the output size and security level of SHA-256 with the performance of SHA-512—but almost no systems use it so far.
From a non-security perspective, the reasons to choose SHA-256 over the longer digests are more easily apparent: it's smaller, requiring less bandwidth to store and transmit, less memory and in many cases less processing power to compute. (There are cases where SHA-512 is faster and more efficient.)
- The ChaCha20 stream cipher is much faster than AES when hardware acceleration is unavailable, while also being extremely secure.It is fast because it exclusively relies on operations that all CPUs natively support: additions, rotations, and XORs

Android support for ECDSA was introduced since version 4.0 using Bouncycastle (v1.46) as the default cryptographic provider. See the blog https://nelenkov.blogspot.com.es/2011/12/using-ecdh-on-android.html?m=1
But Android included a shortened version of Bouncycastle, and there is no full support for ECDSA. You can see in the link that algorithm KeyPairGenerator/ECDSA is not supported, which is the required one to generate ethereum keys.
You can not include directly the bouncycastle library because there is a conflict with the package name org.bouncycastle. I suggest to include spongycastle in your project, which it is a repackaged version of bouncycastle for Android org.spongycastle.

JCA usa abstrações definidas no jce: The basic difference between JCA and JCE is that JCE is an extension of JCA, not a replacement. The JCA includes classes like MessageDigest, SecureRandom, KeyFactory, Signature and KeyStore. JCE add some more classes of cryptography like Cipher, KeyGeneration, Mac and KeyGeneration. The distinction between JCA and JCE has largely faded as the JCE has been provided with the standard runtime for some time now.
JCA/JCE is designed to separate cryptographic implementation from abstraction.
“Since the JCE uses the same architecture as the JCA, the JCE should be more properly thought of as a part of the JCA. - oracle”



No pixel 3a:
- o AndroidOpenSSL tem sha2 fams
- Nao tem bc digest 


### Retirado da documentacao Android

https://android-developers.googleblog.com/2018/03/cryptography-changes-in-android-p.html

Starting in Android P, we plan to deprecate some functionality from the BC provider that's duplicated by the AndroidOpenSSL (also known as Conscrypt) provider. 

To be clear, we aren't doing this because we are concerned about the security of the implementations from the BC provider, rather because having duplicated functionality imposes additional costs and risks while not providing much benefit.


the Crypto provider was deprecated beginning in Android Nougat. Since then, any request for the Crypto provider by an application targeting API 23 (Marshmallow) or before would succeed, but requests by applications targeting API 24 (Nougat) or later would fail. In Android P, we plan to remove the Crypto provider entirely. Once removed, any call to SecureRandom.getInstance("SHA1PRNG", "Crypto") will throw NoSuchProviderException

RSA with proper random encryption padding (like RSAES-OAEP) is believed to give IND-CPA and even IND-CCA2 confidentiality. But it has limited capacity: like 190-byte message for 256-byte cryptogram (using RSA-2048 and SHA-256). Above that limit, ECB can safely be used if one does not care about the large speed penalty (especially for decryption) and significant size penalty due to repeated use of RSAES-OAEP.
RSA without random encryption padding (textbook RSA) is not secure. In particular, it allows to check a guess of the plaintext. Also, care must be taken that a plaintext block should be at least 1 bit less than than the public modulus is.

None of the modes of operation used for symmetric block ciphers make RSA secure:
ECB, CBC, PCBC all inherit the weakness of textbook RSA that a guess of a plaintext block can be trivially verified by re-performing the encryption of that block (which requires the public key only), and comparing with the actual ciphertext block.
CTR, CFB and OFB are totally insecure. Anyone can trivially decipher, since decryption uses the block cipher in encryption mode only.



Most new Android devices have hardware support for AES via the ARMv8 Cryptography Extensions. 

In order to offer low cost options, device manufacturers sometimes use low-end processors such as the ARM Cortex-A7, which does not have hardware support for AES. On these devices, AES is so slow that it would result in a poor user experience; 


https://security.googleblog.com/2019/02/introducing-adiantum-encryption-for.html

Generic and ARM-optimized implementations of Adiantum are available in the Android common kernels v4.9 and higher, and in the mainline Linux kernel v5.0 and higher. Reference code, test vectors, and a benchmarking suite are available at https://github.com/google/adiantum.

Where hardware support for AES exists, AES is faster than Adiantum; 


https://android-developers.googleblog.com/2019/05/queue-hardening-enhancements.html

