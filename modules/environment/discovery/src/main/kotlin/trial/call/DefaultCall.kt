package io.github.junekim0007.cryptobench.discovery.trial.call

import io.github.junekim0007.cryptobench.discovery.contract.DefaultRunOutcome
import java.security.Provider

/** One real call of one engine type with a default key. May throw; the trial records what it throws. */
internal interface DefaultCall {

    val takesInput: Boolean

    fun call(provider: Provider, algorithm: String, input: ByteArray, keys: DefaultKeys): DefaultRunOutcome
}
