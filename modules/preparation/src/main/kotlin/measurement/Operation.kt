package io.github.junekim0007.cryptobench.preparation.measurement

enum class Operation {
    ENCRYPT,
    DECRYPT,
    SIGN,
    VERIFY,
    DIGEST,
    COMPUTE_MAC,
    GENERATE_KEY,
    GENERATE_KEY_PAIR,
    AGREE_KEY,
    TYPE_DEFAULT,
}
