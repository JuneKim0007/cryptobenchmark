package io.github.junekim0007.cryptobench.discovery.trial.requirement

// Per declared alias: the class it runs, whether it behaves as the service did, and whether the key its own name suggests runs on it.
internal object AliasRuns {

    fun of(service: ProbedService, classRun: String, result: CallResult): List<Map<String, Any>> =
        service.entry.aliases.map { alias ->
            val run = ClassRun.of(service.provider, service.type, alias)
            val record = linkedMapOf<String, Any>("name" to alias, "classRun" to run, "sameClass" to (run == classRun))
            result.aliasRuns?.let { check -> record["behaviour"] = ErrorText.refusal { check(alias) } ?: "same" }
            result.aliasAcceptsKey?.let { accepts -> ownNameKey(service, alias, result, accepts)?.let { record["ownNameKey"] = it } }
            record
        }

    private fun ownNameKey(service: ProbedService, alias: String, result: CallResult, accepts: (String, ProbeKey) -> Unit): Map<String, Any>? {
        val own = service.keys.of(service.type, alias, service.provider).firstOrNull { it.source != ProbeKey.RAW } ?: return null
        if (own.source == result.key?.source) return null
        return own.describe() + ("result" to (ErrorText.refusal { accepts(alias, own) } ?: "accepted"))
    }
}
