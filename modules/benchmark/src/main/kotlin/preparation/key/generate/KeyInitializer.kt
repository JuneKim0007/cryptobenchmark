package io.github.junekim0007.cryptobench.benchmark.preparation.key.generate

import java.security.KeyPairGenerator
import java.security.SecureRandom
import java.security.spec.AlgorithmParameterSpec
import javax.crypto.KeyGenerator

/** How one provider's generators are initialised; AndroidKeyStore needs its own, registered from :android. */
interface KeyInitializer {

    fun initialize(generator: KeyGenerator, keySize: Int?, spec: AlgorithmParameterSpec?, random: SecureRandom)

    fun initialize(generator: KeyPairGenerator, keySize: Int?, spec: AlgorithmParameterSpec?, random: SecureRandom)
}
