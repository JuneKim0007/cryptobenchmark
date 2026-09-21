package io.github.junekim0007.cryptobench.preparation.key.generate

import java.security.KeyPairGenerator
import java.security.SecureRandom
import java.security.spec.AlgorithmParameterSpec
import javax.crypto.KeyGenerator

/** A bound key spec when the case has one, else the key size, else the provider's default; randomness always injected. */
object DefaultKeyInitializer : KeyInitializer {

    override fun initialize(generator: KeyGenerator, keySize: Int?, spec: AlgorithmParameterSpec?, random: SecureRandom) {
        when {
            spec != null -> generator.init(spec, random)
            keySize != null -> generator.init(keySize, random)
            else -> generator.init(random)
        }
    }

    override fun initialize(generator: KeyPairGenerator, keySize: Int?, spec: AlgorithmParameterSpec?, random: SecureRandom) {
        when {
            spec != null -> generator.initialize(spec, random)
            keySize != null -> generator.initialize(keySize, random)
        }
    }
}
