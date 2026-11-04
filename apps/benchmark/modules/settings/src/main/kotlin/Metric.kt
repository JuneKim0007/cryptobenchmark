package io.github.junekim0007.cryptobench.settings

/** What a harness measures per case, from run.metrics; TIME is always measured. */
enum class Metric {
    TIME,
    ALLOCATION,
    CPU_EVENTS;

    fun support(facts: Facts): Support = when {
        this != CPU_EVENTS -> Support.Supported
        facts.rooted == null -> Support.NotSupported(facts.unknown("rooted"), required = true)
        facts.rooted == false -> Support.NotSupported("no_root: CPU event counters need a rooted device", required = true)
        else -> Support.Supported
    }

    companion object {

        fun read(names: List<String>, path: String): Set<Metric> {
            val metrics = names.mapTo(LinkedHashSet()) { name ->
                entries.firstOrNull { it.name == name } ?: throw IllegalArgumentException("invalid: $path $name, known ${entries.map { it.name }}")
            }
            require(metrics.size == names.size) { "duplicate: $path $names" }
            require(TIME in metrics) { "missing_metric: $path $names, TIME is always measured" }
            return metrics
        }

        fun unsupported(metrics: Set<Metric>, facts: Facts, path: String): List<Unsupported> = metrics.mapNotNull { metric ->
            (metric.support(facts) as? Support.NotSupported)?.let { Unsupported("$path.${metric.name}", it.reason, it.required) }
        }
    }
}
