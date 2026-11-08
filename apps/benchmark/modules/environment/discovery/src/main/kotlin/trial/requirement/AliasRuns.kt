package io.github.junekim0007.cryptobench.discovery.trial.requirement

import io.github.junekim0007.cryptobench.jca.failure.Attempt
import io.github.junekim0007.cryptobench.jca.failure.ErrorText

// Per declared alias: the class it runs, whether it behaves as the service did, and whether a password key its name suggests runs on it.
internal object AliasRuns {

    fun of(service: ProbedService, classRun: String, result: CallResult): List<Map<String, Any>> =
        service.entry.aliases.map { alias ->
            Attempt.of { record(service, alias, classRun, result) }.getOrElse { linkedMapOf("name" to alias, "error" to ErrorText.of(it)) }
        }

    private fun record(service: ProbedService, alias: String, classRun: String, result: CallResult): Map<String, Any> {
        val run = ClassRun.of(service.provider, service.type, alias)
        val record = linkedMapOf<String, Any>("name" to alias, "classRun" to run, "sameClass" to (run == classRun))
        result.aliasRuns?.let { check -> record["behaviour"] = ErrorText.refusal { check(alias) } ?: "same" }
        result.aliasAcceptsKey?.let { accepts -> ownNameKey(service, alias, result, accepts)?.let { record["ownNameKey"] = it } }
        return record
    }

    private fun ownNameKey(service: ProbedService, alias: String, result: CallResult, accepts: (String, ProbeKey) -> Unit): Map<String, Any>? {
        if (result.key?.source == ProbeKey.FACTORY) return null
        val own = service.keys.of(service.type, alias, service.provider).firstOrNull { it.source == ProbeKey.FACTORY } ?: return null
        return own.describe() + ("result" to (ErrorText.refusal { accepts(alias, own) } ?: "accepted"))
    }
}
