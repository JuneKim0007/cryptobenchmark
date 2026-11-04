package io.github.junekim0007.cryptobench.benchmark.run

import io.github.junekim0007.cryptobench.benchmark.run.energy.Energy
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.settings.CpuSettings
import io.github.junekim0007.cryptobench.settings.HarnessSettings
import io.github.junekim0007.cryptobench.settings.Metric

data class CaseSettings(
    val iterations: Int?,
    val warmupIterations: Int?,
    val profiling: Profiling,
    val metrics: Set<Metric>,
    val energy: Energy = Energy.NONE,
    val cpu: CpuSettings? = null,
) {

    enum class Profiling { NONE, METHOD_TRACING, STACK_SAMPLING }

    companion object {

        fun of(case: BenchmarkCase): CaseSettings = of(case.harness, case.metrics)

        fun of(harness: HarnessSettings, metrics: Set<Metric>): CaseSettings =
            CaseSettings(harness.iterations, harness.warmupIterations, profilingOf(harness.profiling), metrics, Energy.of(harness.energy), harness.cpu)

        private fun profilingOf(name: String?): Profiling = when (name) {
            null, "none" -> Profiling.NONE
            "MethodTracing" -> Profiling.METHOD_TRACING
            "StackSampling" -> Profiling.STACK_SAMPLING
            else -> throw IllegalArgumentException("invalid: profiling $name")
        }
    }
}
