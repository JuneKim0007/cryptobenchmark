package io.github.junekim0007.cryptobench.preparation.key.generate

import java.security.KeyPair
import javax.crypto.SecretKey

sealed class KeyMaterial {

    object None : KeyMaterial()

    data class Secret(val key: SecretKey) : KeyMaterial()

    data class Pairs(val pairs: List<KeyPair>) : KeyMaterial()

    val secretKeyOrNull: SecretKey? get() = (this as? Secret)?.key

    val keyPairsOrNull: List<KeyPair>? get() = (this as? Pairs)?.pairs
}
