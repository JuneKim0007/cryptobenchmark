package io.github.junekim0007.cryptobench.settings

/** The state a case is measured in, from run.phases. */
enum class Phase {
    WARM;

    companion object {

        fun read(names: List<String>, path: String): Set<Phase> {
            require(names.isNotEmpty()) { "missing_field: $path" }
            val phases = names.mapTo(LinkedHashSet()) { name ->
                entries.firstOrNull { it.name == name } ?: throw IllegalArgumentException("unknown_phase: $name, one of ${entries.map { it.name }}")
            }
            require(phases.size == names.size) { "duplicate: $path $names" }
            return phases
        }
    }
}
