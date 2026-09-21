package io.github.junekim0007.cryptobench.benchmark.preparation.key.plan

enum class KeyShape {
    NONE,
    SECRET,
    PAIR,

    /** Own key pair plus a peer's, as a key agreement needs. */
    PEER_PAIRS,

    /** Secret when the device has a KeyGenerator for the key algorithm, pair when it has a KeyPairGenerator. */
    DEVICE_DECIDES,
}
