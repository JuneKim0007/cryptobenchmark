package io.github.junekim0007.cryptobench.benchmark.run

import io.github.junekim0007.cryptobench.benchmark.run.energy.Energy
import io.github.junekim0007.cryptobench.preparation.global.HarnessSettings

data class CaseSettings(val iterations: Int?, val warmupIterations: Int?, val profiling: Profiling, val energy: Energy = Energy.NONE) {

    enum class Profiling { NONE, METHOD_TRACING, STACK_SAMPLING }

    init {
        require(iterations == null || iterations >= 1) { "not_positive: iterations $iterations" }
        // androidx refuses a warm-up count of zero ("must null or positive"); asking for none is not expressible, so it is not accepted
        require(warmupIterations == null || warmupIterations >= 1) {
            "not_supported: warmupIterations $warmupIterations, androidx needs at least 1; leave it out to let the library decide"
        }
    }

    companion object {

        fun of(harness: HarnessSettings): CaseSettings =
            CaseSettings(harness.iterations, harness.warmupIterations, profilingOf(harness.profiling), Energy.of(harness.energy))

        private fun profilingOf(name: String?): Profiling = when (name) {
            null, "none" -> Profiling.NONE
            "MethodTracing" -> Profiling.METHOD_TRACING
            "StackSampling" -> Profiling.STACK_SAMPLING
            else -> throw IllegalArgumentException("invalid: profiling $name")
        }
    }
}
