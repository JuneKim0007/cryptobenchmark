package io.github.junekim0007.cryptobench.settings

/** Pin the measuring thread to one core: an index, or big, resolved from facts. */
data class CpuSettings(val core: CoreChoice? = null, val required: Boolean? = null) {

    val isRequired: Boolean get() = required == true

    /** The core to pin once resolved; null while unset or still big. */
    val index: Int? get() = (core as? CoreChoice.Index)?.index

    fun support(facts: Facts): Support {
        val reason = when {
            core == null -> "no_core: cpu.core is not set"
            facts.pinning == null -> facts.unknown("pinning")
            facts.pinning == false -> "no_pinning: the installed app carries no native affinity library"
            facts.cores == null -> facts.unknown("cpu.cores")
            core == CoreChoice.Big && bigCore(facts) == null -> "no_frequencies: no online core reports a maximum frequency"
            core is CoreChoice.Index && facts.cores.none { it.index == core.index && it.online } -> "no_core: core $core is not an online core of ${facts.cores.map { it.index }}"
            else -> return Support.Supported
        }
        return Support.NotSupported(reason, isRequired)
    }

    fun resolved(facts: Facts): CpuSettings = if (core == CoreChoice.Big) bigCore(facts)?.let { copy(core = CoreChoice.Index(it)) } ?: this else this

    companion object {
        val CPU: Section<CpuSettings> = Section(CpuSettings(), "cpu.") {
            listOf(
                Leaf("core", CoreChoice::read, { it.core }, { o, v -> o.copy(core = v) }, writer = CoreChoice::write),
                Leaf("required", Values.boolean, { it.required }, { o, v -> o.copy(required = v) }),
            )
        }

        /** The online core with the highest maximum frequency; the highest index on a tie. */
        fun bigCore(facts: Facts): Int? = facts.cores
            ?.filter { it.online && it.maxKhz != null }
            ?.maxWithOrNull(compareBy({ it.maxKhz }, { it.index }))?.index
    }
}
