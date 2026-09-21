package io.github.junekim0007.cryptobench.benchmark.preparation.key.generate

import java.security.KeyPairGenerator
import java.security.SecureRandom
import javax.crypto.KeyGenerator

/** Key size when the case names one, the provider's default otherwise; randomness always injected. */
object DefaultKeyInitializer : KeyInitializer {

    override fun initialize(generator: KeyGenerator, keySize: Int?, random: SecureRandom) {
        if (keySize == null) generator.init(random) else generator.init(keySize, random)
    }

    override fun initialize(generator: KeyPairGenerator, keySize: Int?, random: SecureRandom) {
        if (keySize != null) generator.initialize(keySize, random)
    }
}
