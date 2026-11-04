package io.github.junekim0007.cryptobench.preparation.input

import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import java.security.Key

object CipherKeys {

    fun encrypting(key: KeyMaterial): Key = when (key) {
        is KeyMaterial.Secret -> key.key
        is KeyMaterial.Pairs -> key.pairs.first().public
        KeyMaterial.None -> throw IllegalArgumentException("cipher_needs_a_key")
    }

    fun decrypting(key: KeyMaterial): Key = when (key) {
        is KeyMaterial.Secret -> key.key
        is KeyMaterial.Pairs -> key.pairs.first().private
        KeyMaterial.None -> throw IllegalArgumentException("cipher_needs_a_key")
    }
}
