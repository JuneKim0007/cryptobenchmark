package io.github.junekim0007.cryptobench.config.effective

import io.github.junekim0007.cryptobench.config.global.dto.Warmup
import io.github.junekim0007.cryptobench.config.testset.dto.Rule

/** run.warmup.jobs resolved to the effective entries they select, each written as an exact rule the runner compares field by field. */
internal object WarmupJobs {

    fun resolve(warmup: Warmup, providers: Map<String, Map<String, Map<String, *>>>): Pair<Warmup, List<String>> {
        if (warmup.jobs.isEmpty() || warmup.iterations == 0) return warmup to emptyList()
        val entries = providers.flatMap { (provider, types) ->
            types.flatMap { (type, keys) -> keys.keys.map { key -> Entry(provider, type, key.substringBefore('@'), key.substringAfter('@', "").ifEmpty { null }) } }
        }
        val selected = entries.filter { entry -> warmup.jobs.any { entry.selectedBy(it) } }
        val warnings = warmup.jobs.filter { job -> entries.none { it.selectedBy(job) } }.map { "warmup_job_matches_nothing: $it" }
        // No entry selected: the warm-up is off, as the runner would have skipped it.
        return (if (selected.isEmpty()) Warmup(0) else Warmup(warmup.iterations, selected.map { it.rule })) to warnings
    }

    private class Entry(val provider: String, val type: String, val name: String, val group: String?) {
        fun selectedBy(job: Rule): Boolean = job.matches(provider, type, name) && job.appliesTo(group)
        val rule: Rule get() = Rule(provider, type, name, group)
    }
}
