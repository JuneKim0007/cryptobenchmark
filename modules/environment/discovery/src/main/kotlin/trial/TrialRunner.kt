package io.github.junekim0007.cryptobench.discovery.trial

import io.github.junekim0007.cryptobench.discovery.contract.CapturedEnvironment
import io.github.junekim0007.cryptobench.discovery.contract.ServiceEntry
import io.github.junekim0007.cryptobench.discovery.contract.ServiceKey
import io.github.junekim0007.cryptobench.discovery.contract.ServiceTrialEntry
import io.github.junekim0007.cryptobench.discovery.contract.TransformationTrialEntry
import io.github.junekim0007.cryptobench.discovery.contract.TrialOutcome
import io.github.junekim0007.cryptobench.discovery.contract.TrialReport
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
        outcome = Attempt.of { instantiate(provider, service) },
        transformations = if (isCipher(service)) transformations(provider, service) else emptyList(),
    )

    private fun instantiate(provider: Provider, service: ServiceEntry) {
        val registered = provider.getService(service.type, service.algorithm)
            ?: throw NoSuchAlgorithmException("${service.type}.${service.algorithm} is not registered")
        registered.newInstance(null)
    }

    private fun transformations(provider: Provider, service: ServiceEntry): List<TransformationTrialEntry> =
        TransformationSet.of(service).map { transformation ->
            TransformationTrialEntry(transformation, Attempt.of { Cipher.getInstance(transformation, provider) })
        }

    private fun isCipher(service: ServiceEntry): Boolean = ServiceKey.fold(service.type) == CIPHER

    private companion object {
        val CIPHER = ServiceKey.fold("Cipher")
    }
}
