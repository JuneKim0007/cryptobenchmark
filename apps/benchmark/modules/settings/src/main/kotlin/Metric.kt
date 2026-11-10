package io.github.junekim0007.cryptobench.settings

/** What a harness measures per case, from run.metrics; TIME is always measured. */
enum class Metric {
    TIME,
    ALLOCATION;

    companion object {

        fun read(names: List<String>, path: String): Set<Metric> {
            val metrics = names.mapTo(LinkedHashSet()) { name ->
                entries.firstOrNull { it.name == name } ?: throw IllegalArgumentException("invalid: $path $name, known ${entries.map { it.name }}")
            }
            require(metrics.size == names.size) { "duplicate: $path $names" }
            require(TIME in metrics) { "missing_metric: $path $names, TIME is always measured" }
            return metrics
        }
    }
}
