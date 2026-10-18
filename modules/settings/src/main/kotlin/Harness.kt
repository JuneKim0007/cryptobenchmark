package io.github.junekim0007.cryptobench.settings

/** What the timer is told; every key lives in one table below, read, written and merged through it. */
data class HarnessSettings(
    val iterations: Int? = null,
    val warmupIterations: Int? = null,
    val profiling: String? = null,
    val energy: EnergySettings = EnergySettings(),
    val cpu: CpuRequest? = null,
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
                Key("cpu", { value, label, path -> CpuRequest.read(Values.section(value, "$path.cpu"), label) }, { it.cpu }, { o, v -> o.copy(cpu = v) },
                    write = { it.document() }, requires = { request, facts -> request.support(facts) }, drop = { it.copy(cpu = null) },
                    required = { it.required }),
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

/** Pin the measuring thread to one core: an index, or "big" for the highest-frequency online core. */
data class CpuRequest(val core: String, val required: Boolean = false) {
    init {
        require(core == BIG || core.toIntOrNull()?.let { it >= 0 } == true) { "invalid: cpu.core $core, an index or $BIG" }
    }

    fun document(): Map<String, Any> = linkedMapOf("core" to (core.toIntOrNull() ?: core), "required" to required)

    fun support(facts: Facts): Support = when {
        facts.pinning == null || facts.cores == null -> Support.NotSupported("facts_unknown: no facts.yaml for this run")
        facts.pinning == false -> Support.NotSupported("no_pinning: the installed app carries no native affinity library")
        core == BIG && facts.cores.none { it.online && it.maxKhz != null } -> Support.NotSupported("no_frequencies: no online core reports a maximum frequency")
        core != BIG && facts.cores.none { it.index == core.toInt() && it.online } -> Support.NotSupported("no_core: core $core is not an online core of ${facts.cores.map { it.index }}")
        else -> Support.Supported
    }

    companion object {
        const val BIG = "big"

        fun read(document: Map<String, Any>, label: String): CpuRequest {
            val unknown = document.keys - setOf("core", "required")
            require(unknown.isEmpty()) { "unknown_keys: $label $unknown, known [core, required]" }
            val core = document["core"] ?: throw IllegalArgumentException("missing_field: $label.core")
            val required = document["required"] ?: false
            require(required is Boolean) { "wrong_type: $label.required expects true or false" }
            return CpuRequest(core.toString(), required)
        }
    }
}
