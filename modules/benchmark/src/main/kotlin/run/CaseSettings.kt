package io.github.junekim0007.cryptobench.benchmark.run

import io.github.junekim0007.cryptobench.benchmark.run.energy.Energy
import io.github.junekim0007.cryptobench.settings.HarnessSettings

data class CaseSettings(val iterations: Int?, val warmupIterations: Int?, val profiling: Profiling, val energy: Energy = Energy.NONE) {

    enum class Profiling { NONE, METHOD_TRACING, STACK_SAMPLING }

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
