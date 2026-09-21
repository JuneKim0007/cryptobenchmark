package io.github.junekim0007.cryptobench.discovery.setting

object BenchmarkScope {

    val TYPES: Set<String> = linkedSetOf(
        "Cipher", "MessageDigest", "Mac", "Signature",
        "KeyGenerator", "KeyPairGenerator", "KeyAgreement",
    )
}
