package io.github.junekim0007.cryptobench.discovery.trial.requirement

import io.github.junekim0007.cryptobench.discovery.contract.ServiceEntry
import io.github.junekim0007.cryptobench.discovery.contract.ServiceTrialEntry
import java.security.Provider

internal class ProbedService(
    val provider: Provider,
    val type: String,
    val algorithm: String,
    val entry: ServiceEntry,
    val trial: ServiceTrialEntry,
    val keys: KeySources,
    val providers: List<Provider>,
    val digests: List<String>,
    val secretNames: List<String>,
)

/** What a service's own call decided. aliasRuns throws unless the alias behaves as the service did; acceptsKey is the same call on another key. */
internal class CallResult(
    val reason: String = "",
    val detail: String = "",
    val key: ProbeKey? = null,
    val runWith: Map<String, Any> = emptyMap(),
    val keysTried: List<Map<String, Any>> = emptyList(),
    val aliasRuns: ((String) -> Unit)? = null,
    val aliasAcceptsKey: ((String, ProbeKey) -> Unit)? = null,
)

internal interface RequirementCall {

    /** The engine by name: a provider can register a service and still refuse to hand it out. */
    fun instance(service: ProbedService)

    fun measure(service: ProbedService, sheet: FactSheet): CallResult
}
