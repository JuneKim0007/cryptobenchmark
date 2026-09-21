package io.github.junekim0007.cryptobench.benchmark.preparation.key.generate

import java.security.KeyPairGenerator
import java.security.SecureRandom
import javax.crypto.KeyGenerator

/** How one provider's generators are initialised; AndroidKeyStore needs its own, registered from :android. */
interface KeyInitializer {

    fun initialize(generator: KeyGenerator, keySize: Int?, random: SecureRandom)

    fun initialize(generator: KeyPairGenerator, keySize: Int?, random: SecureRandom)
}
