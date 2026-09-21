package io.github.junekim0007.cryptobench.discovery.query

import io.github.junekim0007.cryptobench.discovery.contract.ServiceKey
import io.github.junekim0007.cryptobench.discovery.contract.ServiceTrialEntry
import io.github.junekim0007.cryptobench.discovery.contract.TransformationTrialEntry
import io.github.junekim0007.cryptobench.discovery.contract.TrialReport

/** Questions asked of one trial report. Pure. */
class TrialQuery(private val report: TrialReport) {

    /** The trial of one registered service; null when it was not tried. */
    fun serviceTrial(providerName: String, type: String, algorithm: String): ServiceTrialEntry? {
        val wanted = ServiceKey(type, algorithm)
        return report.services.firstOrNull { it.provider == providerName && ServiceKey(it.type, it.algorithm) == wanted }
    }

    /** The trial of one transformation under a registered cipher service; null when it was not tried. */
    fun transformationTrial(providerName: String, algorithm: String, transformation: String): TransformationTrialEntry? =
        serviceTrial(providerName, CIPHER, algorithm)?.transformations?.firstOrNull { it.name.equals(transformation, ignoreCase = true) }

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

    private companion object {
        const val CIPHER = "Cipher"
    }
}
