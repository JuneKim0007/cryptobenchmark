package io.github.junekim0007.cryptobench.discovery.trial

import io.github.junekim0007.cryptobench.jca.failure.Attempt
import io.github.junekim0007.cryptobench.contract.capture.CapturedEnvironment
import io.github.junekim0007.cryptobench.contract.capture.ServiceEntry
import io.github.junekim0007.cryptobench.discovery.adapter.ServiceKey
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
        val services = capture.providers.flatMap { entry ->
            val provider = installed[entry.name]
            entry.services.map { service ->
                if (provider == null) notInstalled(entry.name, service) else trial(provider, service)
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

    private fun trial(provider: Provider, service: ServiceEntry): ServiceTrialEntry = ServiceTrialEntry(
        provider = provider.name,
        type = service.type,
        algorithm = service.algorithm,
        outcome = TrialOutcome.of(Attempt.of { instantiate(provider, service) }),
        transformations = if (isCipher(service)) transformations(provider, service) else emptyList(),
    )

    private fun instantiate(provider: Provider, service: ServiceEntry) {
        val registered = provider.getService(service.type, service.algorithm)
            ?: throw NoSuchAlgorithmException("${service.type}.${service.algorithm} is not registered")
        registered.newInstance(null)
    }

    private fun transformations(provider: Provider, service: ServiceEntry): List<TransformationTrialEntry> =
        TransformationSet.of(service).map { transformation ->
            TransformationTrialEntry(transformation, TrialOutcome.of(Attempt.of { Cipher.getInstance(transformation, provider) }))
        }

    private fun isCipher(service: ServiceEntry): Boolean = ServiceKey.fold(service.type) == CIPHER

    private companion object {
        val CIPHER = ServiceKey.fold("Cipher")
    }
}
