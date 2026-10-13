package io.github.junekim0007.cryptobench.preparation.global

data class HarnessSettings(
    val iterations: Int? = null,
    val warmupIterations: Int? = null,
    val profiling: String? = null,
    val energy: EnergySettings = EnergySettings(),
) {

    init {
        require(iterations == null || iterations >= 1) { "not_positive: iterations $iterations" }
        require(warmupIterations == null || warmupIterations >= 0) { "negative: warmupIterations $warmupIterations" }
        require(profiling == null || profiling in PROFILING) { "invalid: profiling $profiling, known $PROFILING" }
    }

    fun mergedWith(later: HarnessSettings?): HarnessSettings =
        if (later == null) this else HarnessSettings(
            iterations = later.iterations ?: iterations,
            warmupIterations = later.warmupIterations ?: warmupIterations,
            profiling = later.profiling ?: profiling,
            energy = energy.mergedWith(later.energy),
        )

    companion object {
        val PROFILING: List<String> = listOf("none", "MethodTracing", "StackSampling")
    }
}
