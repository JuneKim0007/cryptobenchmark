package io.github.junekim0007.cryptobench.discovery.trial.call

import io.github.junekim0007.cryptobench.discovery.contract.DefaultRunOutcome
import java.security.Provider
import java.security.Signature

internal object SignatureCall : DefaultCall {

    override val takesInput: Boolean = true

    override fun call(provider: Provider, algorithm: String, input: ByteArray, keys: DefaultKeys): DefaultRunOutcome {
        val pair = keys.pair(provider, KeyNames.signatureKey(algorithm))
        Signature.getInstance(algorithm, provider).apply {
            initSign(pair.keys.private)
            update(input)
        }.sign()
        return DefaultRunOutcome(works = true, keyAlgorithm = pair.algorithm, keyProvider = pair.provider, keySize = KeyBits.of(pair.keys.public))
    }
}
