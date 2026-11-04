package io.github.junekim0007.cryptobench.settings

/** Pin the measuring thread to one core: an index, or "big" for the highest-frequency online core, resolved from facts. */
data class CpuSettings(val core: String? = null, val required: Boolean? = null) {
    init {
        require(core == null || core == BIG || core.toIntOrNull()?.let { it in 0..MAX_CORE } == true) { "invalid: cpu.core $core, an index 0..$MAX_CORE or $BIG" }
    }

    val isRequired: Boolean get() = required == true

    fun support(facts: Facts): Support {
        val reason = when {
            core == null -> "no_core: cpu.core is not set"
            facts.pinning == null -> facts.unknown("pinning")
            facts.pinning == false -> "no_pinning: the installed app carries no native affinity library"
            facts.cores == null -> facts.unknown("cpu.cores")
            core == BIG && bigCore(facts) == null -> "no_frequencies: no online core reports a maximum frequency"
            core != BIG && facts.cores.none { it.index == core.toInt() && it.online } -> "no_core: core $core is not an online core of ${facts.cores.map { it.index }}"
            else -> return Support.Supported
        }
        return Support.NotSupported(reason, isRequired)
    }

    fun resolved(facts: Facts): CpuSettings = if (core == BIG) copy(core = bigCore(facts)?.toString() ?: core) else this

    companion object {
        const val BIG = "big"
        const val MAX_CORE = 63

        val CPU: Section<CpuSettings> = Section(CpuSettings(), "cpu.") {
            listOf(
                Leaf("core", Values.word, { it.core }, { o, v -> o.copy(core = v) }, writer = { it.toIntOrNull() ?: it }),
                Leaf("required", Values.boolean, { it.required }, { o, v -> o.copy(required = v) }),
            )
        }

        /** The online core with the highest maximum frequency; the highest index on a tie. */
        fun bigCore(facts: Facts): Int? = facts.cores
            ?.filter { it.online && it.maxKhz != null }
            ?.maxWithOrNull(compareBy({ it.maxKhz }, { it.index }))?.index
    }
}
