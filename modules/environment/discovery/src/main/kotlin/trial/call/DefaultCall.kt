package io.github.junekim0007.cryptobench.discovery.trial.call

import io.github.junekim0007.cryptobench.discovery.contract.DefaultRunOutcome
import java.security.Provider

internal interface DefaultCall {

    val takesInput: Boolean

    fun call(provider: Provider, algorithm: String, input: ByteArray, keys: DefaultKeys): DefaultRunOutcome
}
