package io.github.junekim0007.cryptobench.discovery.trial.call

import io.github.junekim0007.cryptobench.discovery.contract.DefaultRunOutcome
import java.security.KeyPairGenerator
import java.security.Provider
import javax.crypto.KeyGenerator

/** Generation is the measured call itself: the key size recorded is the provider's own default. */
internal class GeneratorCall(private val pair: Boolean) : DefaultCall {

    override val takesInput: Boolean = false

    override fun call(provider: Provider, algorithm: String, input: ByteArray, keys: DefaultKeys): DefaultRunOutcome {
        val key = if (pair) {
            KeyPairGenerator.getInstance(algorithm, provider).generateKeyPair().public
        } else {
            KeyGenerator.getInstance(algorithm, provider).generateKey()
        }
        return DefaultRunOutcome(works = true, keySize = KeyBits.of(key))
    }
}
