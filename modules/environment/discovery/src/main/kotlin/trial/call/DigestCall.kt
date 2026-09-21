package io.github.junekim0007.cryptobench.discovery.trial.call

import io.github.junekim0007.cryptobench.discovery.contract.DefaultRunOutcome
import java.security.MessageDigest
import java.security.Provider

internal object DigestCall : DefaultCall {

    override val takesInput: Boolean = true

    override fun call(provider: Provider, algorithm: String, input: ByteArray, keys: DefaultKeys): DefaultRunOutcome {
        MessageDigest.getInstance(algorithm, provider).digest(input)
        return DefaultRunOutcome(works = true)
    }
}
