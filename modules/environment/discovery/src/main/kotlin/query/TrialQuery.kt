package io.github.junekim0007.cryptobench.discovery.query

import io.github.junekim0007.cryptobench.discovery.contract.ServiceTrialEntry
import io.github.junekim0007.cryptobench.discovery.contract.TrialReport

/** Questions asked of one trial report. Pure. */
class TrialQuery(private val report: TrialReport) {

    /** Registered, and not constructible. */
    fun failingServices(): List<ServiceTrialEntry> =
        report.services.filter { !it.outcome.instantiates }

    /** Declared as mode × padding by the provider, refused by Cipher.getInstance. */
    fun failingTransformations(): List<TransformationFailure> =
        report.services.flatMap { service ->
            service.transformations
                .filter { !it.outcome.instantiates }
                .map { TransformationFailure(service.provider, service.algorithm, it.name, it.outcome.error) }
        }

    /** Provider → how many of its services instantiate, out of how many registered. */
    fun instantiationByProvider(): Map<String, Pair<Int, Int>> =
        report.services.groupBy { it.provider }.mapValues { (_, services) ->
            services.count { it.outcome.instantiates } to services.size
        }
}
