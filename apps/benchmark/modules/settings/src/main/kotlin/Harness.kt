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
