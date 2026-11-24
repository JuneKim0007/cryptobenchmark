package io.github.junekim0007.cryptobench.discovery.trial.requirement

import io.github.junekim0007.cryptobench.discovery.trial.EngineTypes
import io.github.junekim0007.cryptobench.document.names.AlgorithmNames
import io.github.junekim0007.cryptobench.jca.failure.Attempt
import io.github.junekim0007.cryptobench.contract.capture.CapturedEnvironment
import io.github.junekim0007.cryptobench.jca.failure.ErrorText
import io.github.junekim0007.cryptobench.contract.requirements.RequirementReport
import io.github.junekim0007.cryptobench.contract.capture.ServiceEntry
import io.github.junekim0007.cryptobench.contract.requirements.ServiceRequirement
import io.github.junekim0007.cryptobench.contract.trial.ServiceTrialEntry
import io.github.junekim0007.cryptobench.contract.trial.TrialReport
import io.github.junekim0007.cryptobench.discovery.trial.call.DefaultKeys
import java.security.Provider

// Level 3: every registered service gets a record, whatever happens to its neighbours.
class RequirementTrial {

    internal fun run(capture: CapturedEnvironment, trial: TrialReport, providers: Array<Provider>?, keys: DefaultKeys): RequirementReport {
        val started = System.nanoTime()
        val live = providers.orEmpty().toList()
        val installed = live.associateBy { it.name }
        val sources = KeySources(live, keys)
        val digests = namesOf(capture, EngineTypes.DIGEST)
        val secretNames = namesOf(capture, EngineTypes.GENERATOR)
        val trialled = trial.services.associateBy { Triple(it.provider, AlgorithmNames.fold(it.type), AlgorithmNames.fold(it.algorithm)) }
        val services = capture.providers.flatMap { entry ->
            entry.services.flatMap { service ->
                val attempt = trialled.getValue(Triple(entry.name, AlgorithmNames.fold(service.type), AlgorithmNames.fold(service.algorithm)))
                listOf(record(entry.name, installed[entry.name], service, attempt, sources, live, digests, secretNames, "")) +
                    attempt.transformations.filter { it.outcome.instantiates }.map { transformation ->
                        val own = attempt.copy(algorithm = transformation.name, defaultRun = transformation.defaultRun, transformations = emptyList())
                        record(entry.name, installed[entry.name], service.copy(algorithm = transformation.name, aliases = emptyList()), own, sources, live, digests, secretNames, service.algorithm)
                    }
            }
        }
        return RequirementReport(
            capturedAtMillis = capture.capturedAtMillis,
            deviceClockMillis = capture.deviceClockMillis,
            services = KeyOrigin.applied(services),
            millis = (System.nanoTime() - started) / NANOS_PER_MILLI,
            keyCache = keys.stats(),
        )
    }

    private fun record(
        providerName: String,
        provider: Provider?,
        service: ServiceEntry,
        attempt: ServiceTrialEntry,
        sources: KeySources,
        live: List<Provider>,
        digests: List<String>,
        secretNames: List<String>,
        transformationOf: String,
    ): ServiceRequirement {
        val started = System.nanoTime()
        val base = ServiceRequirement(providerName, service.type, service.algorithm, ServiceRequirement.NO_CALL, service.className, transformationOf = transformationOf, reason = ServiceRequirement.NO_CALL_FOR_TYPE)
        return Attempt.of { measured(base, provider, service, attempt, sources, live, digests, secretNames, started) }
            .getOrElse { base.copy(status = ServiceRequirement.NOT_RUNNABLE, reason = ServiceRequirement.PROBE_FAILED, detail = ErrorText.of(it)) }
    }

    private fun measured(
        base: ServiceRequirement,
        provider: Provider?,
        service: ServiceEntry,
        attempt: ServiceTrialEntry,
        sources: KeySources,
        live: List<Provider>,
        digests: List<String>,
        secretNames: List<String>,
        started: Long,
    ): ServiceRequirement {
        val transformationOf = base.transformationOf
        if (provider == null) return base.copy(status = ServiceRequirement.NOT_RUNNABLE, reason = ServiceRequirement.PROVIDER_NOT_INSTALLED)
        if (!attempt.outcome.instantiates) {
            return base.copy(status = ServiceRequirement.NOT_RUNNABLE, reason = ServiceRequirement.INSTANTIATION_FAILED, detail = ErrorText.clean(attempt.outcome.error))
        }
        val classRun = if (transformationOf.isEmpty()) ClassRun.of(provider, service.type, service.algorithm) else ""
        val call = RequirementCalls.of(service.type) ?: return base.copy(classRun = classRun)
        val probed = ProbedService(provider, service.type, service.algorithm, service, attempt, sources, live, digests, secretNames)
        ErrorText.refusal { call.instance(probed) }?.let {
            return base.copy(status = ServiceRequirement.NOT_RUNNABLE, classRun = classRun, reason = ServiceRequirement.INSTANCE_REFUSED, detail = it)
        }
        val sheet = FactSheet()
        val result = Attempt.of { call.measure(probed, sheet) }
            .getOrElse { CallResult(ServiceRequirement.PROBE_FAILED, ErrorText.of(it)) }
        return base.copy(
            status = if (result.reason.isEmpty()) ServiceRequirement.RUNNABLE else ServiceRequirement.NOT_RUNNABLE,
            classRun = classRun,
            reason = result.reason,
            detail = result.detail,
            key = result.key?.describe().orEmpty(),
            runWith = result.runWith,
            keysTried = sources.refusals(service.type, service.algorithm, provider) + result.keysTried,
            facts = sheet.facts,
            aliases = AliasRuns.of(probed, classRun, result),
            millis = (System.nanoTime() - started) / NANOS_PER_MILLI,
        )
    }

    private fun namesOf(capture: CapturedEnvironment, type: String): List<String> =
        capture.providers.flatMap { it.services }.filter { AlgorithmNames.fold(it.type) == type }.map { it.algorithm }.distinctBy { AlgorithmNames.fold(it) }

    private companion object {
        const val NANOS_PER_MILLI = 1_000_000L
    }
}
