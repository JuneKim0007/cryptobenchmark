package io.github.junekim0007.cryptobench.discovery.trial

import io.github.junekim0007.cryptobench.jca.failure.Attempt
import io.github.junekim0007.cryptobench.contract.capture.CapturedEnvironment
import io.github.junekim0007.cryptobench.contract.capture.ProviderEntry
import io.github.junekim0007.cryptobench.contract.capture.ServiceEntry
import io.github.junekim0007.cryptobench.contract.trial.ServiceTrialEntry
import io.github.junekim0007.cryptobench.contract.trial.TransformationTrialEntry
import io.github.junekim0007.cryptobench.contract.trial.TrialOutcome
import io.github.junekim0007.cryptobench.contract.trial.TrialReport
import java.security.NoSuchAlgorithmException
import java.security.Provider
import javax.crypto.Cipher

class TrialRunner {

    fun run(capture: CapturedEnvironment, providers: Array<Provider>?): TrialReport {
        val installed = providers.orEmpty().associateBy { it.name }
        val transformations = TransformationSet(capture)
        val services = capture.providers.flatMap { entry ->
            val provider = installed[entry.name]
            entry.services.map { service ->
                if (provider == null) notInstalled(entry.name, service) else trial(provider, entry, service, transformations)
            }
        }
        return TrialReport(capturedAtMillis = capture.capturedAtMillis, services = services)
    }

    private fun notInstalled(providerName: String, service: ServiceEntry): ServiceTrialEntry = ServiceTrialEntry(
        provider = providerName,
        type = service.type,
        algorithm = service.algorithm,
        outcome = TrialOutcome.failure("provider_not_installed"),
    )

    private fun trial(provider: Provider, entry: ProviderEntry, service: ServiceEntry, set: TransformationSet): ServiceTrialEntry = ServiceTrialEntry(
        provider = provider.name,
        type = service.type,
        algorithm = service.algorithm,
        outcome = TrialOutcome.of(Attempt.of { instantiate(provider, service) }),
        transformations = if (TransformationSet.isCipher(service)) transformations(provider, set.of(entry, service)) else emptyList(),
    )

    private fun instantiate(provider: Provider, service: ServiceEntry) {
        val registered = provider.getService(service.type, service.algorithm)
            ?: throw NoSuchAlgorithmException("${service.type}.${service.algorithm} is not registered")
        registered.newInstance(null)
    }

    private fun transformations(provider: Provider, names: List<String>): List<TransformationTrialEntry> =
        names.map { transformation ->
            TransformationTrialEntry(transformation, TrialOutcome.of(Attempt.of { Cipher.getInstance(transformation, provider) }))
        }
}
