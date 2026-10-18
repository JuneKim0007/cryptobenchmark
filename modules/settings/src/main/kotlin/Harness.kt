package io.github.junekim0007.cryptobench.settings

/** What the timer is told; every key lives in one table below, read, written and merged through it. */
data class HarnessSettings(
    val iterations: Int? = null,
    val warmupIterations: Int? = null,
    val profiling: String? = null,
    val energy: EnergySettings = EnergySettings(),
    val cpu: CpuSettings? = null,
) {
    init {
        require(iterations == null || iterations >= 1) { "not_positive: iterations $iterations" }
        require(warmupIterations == null || warmupIterations >= 1) {
            "not_supported: warmupIterations $warmupIterations, androidx needs at least 1; leave it out to let the library decide"
        }
        require(profiling == null || profiling in PROFILING) { "invalid: profiling $profiling, known $PROFILING" }
    }

    val isEmpty: Boolean get() = this == HarnessSettings()

    fun mergedWith(later: HarnessSettings?): HarnessSettings = HARNESS.merged(this, later)

    companion object {
        val PROFILING: List<String> = listOf("none", "MethodTracing", "StackSampling")

        val HARNESS: Section<HarnessSettings> = Section(HarnessSettings(), "") {
            listOf(
                Leaf("iterations", Values.int, { it.iterations }, { o, v -> o.copy(iterations = v) }),
                Leaf("warmupIterations", Values.int, { it.warmupIterations }, { o, v -> o.copy(warmupIterations = v) }),
                Leaf("profiling", Values.text(PROFILING), { it.profiling }, { o, v -> o.copy(profiling = v) }),
                Nested("energy", EnergySettings.ENERGY, { it.energy.takeUnless { e -> e.isEmpty } }, { o, v -> o.copy(energy = v ?: EnergySettings()) }),
                Nested("cpu", CpuSettings.CPU, { it.cpu }, { o, v -> o.copy(cpu = v) },
                    requires = { cpu, facts -> cpu.support(facts) }, resolve = { cpu, facts -> cpu.resolved(facts) }),
            )
        }

        fun read(document: Map<String, Any>?, path: String): HarnessSettings = HARNESS.read(document, path)

        fun write(settings: HarnessSettings): Map<String, Any> = HARNESS.write(settings)
    }
}

data class EnergySettings(
    val capture: String? = null,
    val windowSeconds: Int? = null,
    val warmupSeconds: Int? = null,
    val cooldownSeconds: Int? = null,
) {
    init {
        require(capture == null || capture in CAPTURES) { "invalid: energy.capture $capture, known $CAPTURES" }
        require(windowSeconds == null || windowSeconds >= 1) { "not_positive: energy.windowSeconds $windowSeconds" }
        require(warmupSeconds == null || warmupSeconds >= 1) { "not_positive: energy.warmupSeconds $warmupSeconds" }
        require(cooldownSeconds == null || cooldownSeconds >= 0) { "negative: energy.cooldownSeconds $cooldownSeconds" }
    }

    val isEmpty: Boolean get() = this == EnergySettings()

    fun mergedWith(later: EnergySettings?): EnergySettings = ENERGY.merged(this, later)

    companion object {
        val CAPTURES: List<String> = listOf("none", "measured", "dry")

        val ENERGY: Section<EnergySettings> = Section(EnergySettings(), "energy.") {
            listOf(
                Leaf("capture", Values.text(CAPTURES), { it.capture }, { o, v -> o.copy(capture = v) }),
                Leaf("windowSeconds", Values.int, { it.windowSeconds }, { o, v -> o.copy(windowSeconds = v) }),
                Leaf("warmupSeconds", Values.int, { it.warmupSeconds }, { o, v -> o.copy(warmupSeconds = v) }),
                Leaf("cooldownSeconds", Values.int, { it.cooldownSeconds }, { o, v -> o.copy(cooldownSeconds = v) }),
            )
        }
    }
}

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
