package io.github.junekim0007.cryptobench.discovery.trial.call

import io.github.junekim0007.cryptobench.discovery.contract.DefaultRunOutcome
import java.security.Provider
import javax.crypto.Mac

internal object MacCall : DefaultCall {

    override val takesInput: Boolean = true

    override fun call(provider: Provider, algorithm: String, input: ByteArray, keys: DefaultKeys): DefaultRunOutcome {
        val secret = keys.secret(provider, algorithm)
        Mac.getInstance(algorithm, provider).apply { init(secret.key) }.doFinal(input)
        return DefaultRunOutcome(works = true, keyAlgorithm = secret.algorithm, keyProvider = secret.provider, keySize = KeyBits.of(secret.key))
    }
}
