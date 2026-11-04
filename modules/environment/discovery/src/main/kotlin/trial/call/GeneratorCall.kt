package io.github.junekim0007.cryptobench.discovery.trial.call

import io.github.junekim0007.cryptobench.discovery.contract.DefaultRunOutcome
import java.security.KeyPairGenerator
import java.security.Provider
import javax.crypto.KeyGenerator

internal class GeneratorCall(private val pair: Boolean) : DefaultCall {

    override val takesInput: Boolean = false

    override fun call(provider: Provider, algorithm: String, input: ByteArray, keys: DefaultKeys): DefaultRunOutcome {
        val (key, secret) = if (pair) {
            KeyPairGenerator.getInstance(algorithm, provider).generateKeyPair().let { it.public to it.private }
        } else {
            KeyGenerator.getInstance(algorithm, provider).generateKey().let { it to it }
        }
        val material = if (secret.encoded == null) DefaultRunOutcome.NON_EXPORTABLE else DefaultRunOutcome.EXPORTABLE
        return DefaultRunOutcome(works = true, keySize = KeyBits.of(key), keyMaterial = material, keyFormat = secret.format.orEmpty())
    }
}
