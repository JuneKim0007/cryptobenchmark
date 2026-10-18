package io.github.junekim0007.cryptobench.settings

/** What the timer is told; every key lives in one table below, read, written and merged through it. */
data class HarnessSettings(
    val iterations: Int? = null,
    val warmupIterations: Int? = null,
    val profiling: String? = null,
    val energy: EnergySettings = EnergySettings(),
) {
    init {
        require(iterations == null || iterations >= 1) { "not_positive: iterations $iterations" }
        require(warmupIterations == null || warmupIterations >= 1) { "not_supported: warmupIterations $warmupIterations$WARMUP_HINT" }
        require(profiling == null || profiling in PROFILING) { "invalid: profiling $profiling, known $PROFILING" }
    }

    val isEmpty: Boolean get() = this == HarnessSettings()

    fun mergedWith(later: HarnessSettings?): HarnessSettings = HARNESS.merged(this, later)

    companion object {
        val PROFILING: List<String> = listOf("none", "MethodTracing", "StackSampling")
        private const val WARMUP_HINT = ", androidx needs at least 1; leave it out to let the library decide"

        val HARNESS: Section<HarnessSettings> = Section(HarnessSettings(), "") {
            listOf(
                Key.value("iterations", Values.int(1, "not_positive"), { it.iterations }, { o, v -> o.copy(iterations = v) }),
                Key.value("warmupIterations", Values.int(1, "not_supported", WARMUP_HINT), { it.warmupIterations }, { o, v -> o.copy(warmupIterations = v) }),
                Key.value("profiling", Values.choice(PROFILING), { it.profiling }, { o, v -> o.copy(profiling = v) }),
                Key.section("energy", EnergySettings.ENERGY, { it.energy.takeUnless { e -> e.isEmpty } }, { o, v -> o.copy(energy = v) }),
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
                Key.value("capture", Values.choice(CAPTURES), { it.capture }, { o, v -> o.copy(capture = v) }),
                Key.value("windowSeconds", Values.int(1, "not_positive"), { it.windowSeconds }, { o, v -> o.copy(windowSeconds = v) }),
                Key.value("warmupSeconds", Values.int(1, "not_positive"), { it.warmupSeconds }, { o, v -> o.copy(warmupSeconds = v) }),
                Key.value("cooldownSeconds", Values.int(0, "negative"), { it.cooldownSeconds }, { o, v -> o.copy(cooldownSeconds = v) }),
            )
        }
    }
}
