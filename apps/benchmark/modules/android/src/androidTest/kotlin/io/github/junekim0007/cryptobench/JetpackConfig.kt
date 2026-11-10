package io.github.junekim0007.cryptobench

import androidx.benchmark.ExperimentalBenchmarkConfigApi
import androidx.benchmark.MicrobenchmarkConfig
import androidx.benchmark.ProfilerConfig
import androidx.benchmark.TimeCapture
import io.github.junekim0007.cryptobench.benchmark.run.CaseSettings
import io.github.junekim0007.cryptobench.benchmark.run.energy.Energy
import io.github.junekim0007.cryptobench.settings.Metric

@OptIn(ExperimentalBenchmarkConfigApi::class)
internal object JetpackConfig {

    val METRICS: Set<Metric> = Metric.entries.toSet()

    // Only the energy pass measures energy (PassArguments.applied), and it alone keeps the trace and skips the collection between samples.
    fun measuresEnergy(settings: CaseSettings): Boolean = settings.energy.capture == Energy.Capture.MEASURED

    // An allocation pass adds its own capture beside the time capture.
    fun of(settings: CaseSettings): MicrobenchmarkConfig {
        val profiler = when (settings.profiling) {
            CaseSettings.Profiling.NONE -> null
            CaseSettings.Profiling.METHOD_TRACING -> ProfilerConfig.MethodTracing()
            CaseSettings.Profiling.STACK_SAMPLING -> ProfilerConfig.StackSampling()
        }
        val captures = if (PassArguments.countsAllocations) listOf(TimeCapture(), SampledAllocations()) else MicrobenchmarkConfig().metrics
        val cleaning = if (measuresEnergy(settings)) emptyList() else listOf(CleaningCapture())
        return MicrobenchmarkConfig(metrics = captures + cleaning, profiler = profiler,
            warmupCount = settings.warmupIterations, measurementCount = settings.iterations)
    }
}
