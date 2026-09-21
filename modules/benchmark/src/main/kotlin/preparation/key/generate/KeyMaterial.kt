package io.github.junekim0007.cryptobench.benchmark.preparation.key.generate

import java.security.KeyPair
import javax.crypto.SecretKey

sealed class KeyMaterial {

    object None : KeyMaterial()

    data class Secret(val key: SecretKey) : KeyMaterial()

    /** One pair, or own pair first and peer pair second for a key agreement. */
    data class Pairs(val pairs: List<KeyPair>) : KeyMaterial()
}
