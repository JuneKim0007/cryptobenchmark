package io.github.junekim0007.cryptobench.config.harness

data class HarnessSettings(
    val iterations: Int? = null,
    val warmupIterations: Int? = null,
    val profiling: String? = null,
) {

    init {
        require(iterations == null || iterations >= 1) { "not_positive: iterations $iterations" }
        require(warmupIterations == null || warmupIterations >= 0) { "negative: warmupIterations $warmupIterations" }
        require(profiling == null || profiling in PROFILING) { "invalid: profiling $profiling, known $PROFILING" }
    }

    val isEmpty: Boolean get() = iterations == null && warmupIterations == null && profiling == null

    fun mergedWith(later: HarnessSettings?): HarnessSettings =
        if (later == null) this else HarnessSettings(
            iterations = later.iterations ?: iterations,
            warmupIterations = later.warmupIterations ?: warmupIterations,
            profiling = later.profiling ?: profiling,
        )

    companion object {
        val PROFILING: List<String> = listOf("none", "MethodTracing", "StackSampling")
    }
}
