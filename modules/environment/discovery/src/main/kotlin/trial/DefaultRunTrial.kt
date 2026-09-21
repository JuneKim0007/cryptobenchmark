package io.github.junekim0007.cryptobench.discovery.trial

import io.github.junekim0007.cryptobench.discovery.contract.DefaultRunOutcome
import io.github.junekim0007.cryptobench.discovery.contract.ServiceTrialEntry
import io.github.junekim0007.cryptobench.discovery.contract.TrialReport
import io.github.junekim0007.cryptobench.discovery.trial.call.DefaultCall
import io.github.junekim0007.cryptobench.discovery.trial.call.DefaultCalls
import io.github.junekim0007.cryptobench.discovery.trial.call.DefaultKeys
import java.security.Provider

class DefaultRunTrial(private val inputSizes: List<Int> = listOf(1024, 32)) {

    init {
        require(inputSizes.isNotEmpty() && inputSizes.all { it >= 0 }) { "invalid_input_sizes: $inputSizes" }
    }

    fun run(report: TrialReport, providers: Array<Provider>?): TrialReport {
        val installed = providers.orEmpty().associateBy { it.name }
        val keys = DefaultKeys(providers.orEmpty().toList())
        return report.copy(services = report.services.map { service -> withDefaultRun(service, installed[service.provider], keys) })
    }

    private fun withDefaultRun(service: ServiceTrialEntry, provider: Provider?, keys: DefaultKeys): ServiceTrialEntry {
        val call = DefaultCalls.of(service.type)
        if (call == null || provider == null || !service.outcome.instantiates) {
            return service
        }
        return service.copy(
            defaultRun = run(call, provider, service.algorithm, keys),
            transformations = service.transformations.map { transformation ->
                if (!transformation.outcome.instantiates || transformation.name.equals(service.algorithm, ignoreCase = true)) {
                    transformation
                } else {
                    transformation.copy(defaultRun = run(call, provider, transformation.name, keys))
                }
            },
        )
    }

    private fun run(call: DefaultCall, provider: Provider, algorithm: String, keys: DefaultKeys): DefaultRunOutcome {
        val sizes: List<Int?> = if (call.takesInput) inputSizes else listOf(null)
        var firstFailure: DefaultRunOutcome? = null
        for (size in sizes) {
            val outcome = attempt { call.call(provider, algorithm, ByteArray(size ?: 0), keys).copy(inputSize = size) }
            if (outcome.works) {
                return outcome
            }
            if (firstFailure == null) {
                firstFailure = outcome.copy(inputSize = size)
            }
        }
        return firstFailure!!
    }

    private fun attempt(block: () -> DefaultRunOutcome): DefaultRunOutcome =
        try {
            block()
        } catch (exception: Exception) {
            DefaultRunOutcome.failure(exception)
        } catch (linkageError: LinkageError) {
            DefaultRunOutcome.failure(linkageError)
        }
}
