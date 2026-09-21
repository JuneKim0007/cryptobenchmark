package io.github.junekim0007.cryptobench.preparation.key.generate

import java.security.KeyPairGenerator
import java.security.SecureRandom
import java.security.spec.AlgorithmParameterSpec
import javax.crypto.KeyGenerator

interface KeyInitializer {

    fun initialize(generator: KeyGenerator, keySize: Int?, spec: AlgorithmParameterSpec?, random: SecureRandom)

    fun initialize(generator: KeyPairGenerator, keySize: Int?, spec: AlgorithmParameterSpec?, random: SecureRandom)
}
