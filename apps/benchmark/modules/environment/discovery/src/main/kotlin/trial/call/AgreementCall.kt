package io.github.junekim0007.cryptobench.discovery.trial.call

import io.github.junekim0007.cryptobench.discovery.contract.DefaultRunOutcome
import java.security.Provider
import javax.crypto.KeyAgreement

internal object AgreementCall : DefaultCall {

    override val takesInput: Boolean = false

    override fun call(provider: Provider, algorithm: String, input: ByteArray, keys: DefaultKeys): DefaultRunOutcome {
        val own = keys.pair(provider, KeyNames.agreementKey(algorithm))
        KeyAgreement.getInstance(algorithm, provider).apply {
            init(own.keys.private)
            doPhase(keys.peer(own).public, true)
        }.generateSecret()
        return DefaultRunOutcome(works = true, keyAlgorithm = own.algorithm, keyProvider = own.provider, keySize = KeyBits.of(own.keys.public))
    }
}
