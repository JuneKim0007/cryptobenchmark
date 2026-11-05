package io.github.junekim0007.cryptobench.discovery.trial.requirement

import io.github.junekim0007.cryptobench.discovery.contract.CapturedEnvironment
import io.github.junekim0007.cryptobench.discovery.contract.RequirementReport
import io.github.junekim0007.cryptobench.discovery.contract.ServiceEntry
import io.github.junekim0007.cryptobench.discovery.contract.ServiceKey
import io.github.junekim0007.cryptobench.discovery.contract.ServiceRequirement
import io.github.junekim0007.cryptobench.discovery.contract.ServiceTrialEntry
import io.github.junekim0007.cryptobench.discovery.contract.TrialReport
import io.github.junekim0007.cryptobench.discovery.trial.call.DefaultKeys
import java.security.Provider

// Level 3: every registered service gets a record, whatever happens to its neighbours.
class RequirementTrial {

    internal fun run(capture: CapturedEnvironment, trial: TrialReport, providers: Array<Provider>?, keys: DefaultKeys): RequirementReport {
        val started = System.nanoTime()
        val live = providers.orEmpty().toList()
        val installed = live.associateBy { it.name }
        val sources = KeySources(capture, live, keys)
        val digests = namesOf(capture, DIGEST)
        val secretNames = namesOf(capture, SECRET_GENERATOR)
        val trialled = trial.services.associateBy { Triple(it.provider, ServiceKey.fold(it.type), ServiceKey.fold(it.algorithm)) }
        val services = capture.providers.flatMap { entry ->
            entry.services.flatMap { service ->
                val attempt = trialled.getValue(Triple(entry.name, ServiceKey.fold(service.type), ServiceKey.fold(service.algorithm)))
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
        if (provider == null) return base.copy(status = ServiceRequirement.NOT_RUNNABLE, reason = ServiceRequirement.PROVIDER_NOT_INSTALLED)
        if (!attempt.outcome.instantiates) {
            return base.copy(status = ServiceRequirement.NOT_RUNNABLE, reason = ServiceRequirement.INSTANTIATION_FAILED, detail = ErrorText.clean(attempt.outcome.error))
        }
        val classRun = if (transformationOf.isEmpty()) ClassRun.of(provider, service.type, service.algorithm) else ""
        val call = RequirementCalls.of(service.type) ?: return base.copy(classRun = classRun)
        val probed = ProbedService(provider, service.type, service.algorithm, service, attempt, sources, live, digests, secretNames)
        val sheet = FactSheet()
        val result = runCatching { call.measure(probed, sheet) }
            .getOrElse { CallResult(ServiceRequirement.PROBE_FAILED, ErrorText.of(it)) }
        return base.copy(
            status = if (result.reason.isEmpty()) ServiceRequirement.RUNNABLE else ServiceRequirement.NOT_RUNNABLE,
            classRun = classRun,
            reason = result.reason,
            detail = result.detail,
            key = result.key?.describe().orEmpty(),
            runWith = result.runWith,
            keysTried = result.keysTried,
            facts = sheet.facts,
            aliases = runCatching { AliasRuns.of(probed, classRun, result) }.getOrDefault(emptyList()),
            millis = (System.nanoTime() - started) / NANOS_PER_MILLI,
        )
    }

    private fun namesOf(capture: CapturedEnvironment, type: String): List<String> =
        capture.providers.flatMap { it.services }.filter { ServiceKey.fold(it.type) == type }.map { it.algorithm }.distinctBy { ServiceKey.fold(it) }

    private companion object {
        val DIGEST = ServiceKey.fold("MessageDigest")
        val SECRET_GENERATOR = ServiceKey.fold("KeyGenerator")
        const val NANOS_PER_MILLI = 1_000_000L
    }
}
