package io.github.junekim0007.cryptobench

import androidx.benchmark.ExperimentalBenchmarkConfigApi
import androidx.benchmark.MicrobenchmarkConfig
import androidx.benchmark.ProfilerConfig
import androidx.benchmark.TimeCapture
import androidx.test.platform.app.InstrumentationRegistry
import io.github.junekim0007.cryptobench.benchmark.run.CaseSettings
import io.github.junekim0007.cryptobench.benchmark.run.energy.Energy
import io.github.junekim0007.cryptobench.settings.Metric

@OptIn(ExperimentalBenchmarkConfigApi::class)
internal object JetpackConfig {

    // Paired with apps/benchmark-runner/device/adb.py CPU_EVENTS.
    private const val CPU_EVENT_COUNTER = "androidx.benchmark.cpuEventCounter.enable"

    val METRICS: Set<Metric> = Metric.entries.toSet()

    // Only the energy pass measures energy (PassArguments.applied), and it alone keeps the trace and skips the collection between samples.
    fun measuresEnergy(settings: CaseSettings): Boolean = settings.energy.capture == Energy.Capture.MEASURED

    // MicrobenchmarkConfig's default list carries the CPU event capture when the launch argument enabled it; an allocation pass adds its own.
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

    // Checks the launch argument, not androidx's own decision; a counter androidx drops anyway fails the conversion.
    fun counterMismatch(settings: CaseSettings): String? {
        val counting = (InstrumentationRegistry.getArguments().getString(CPU_EVENT_COUNTER) ?: "false").toBoolean()
        return when {
            Metric.CPU_EVENTS in settings.metrics && !counting ->
                "not_supported: CPU_EVENTS, the launch argument $CPU_EVENT_COUNTER is not true"
            Metric.CPU_EVENTS !in settings.metrics && counting ->
                "not_requested: $CPU_EVENT_COUNTER is true but run.metrics has no CPU_EVENTS"
            else -> null
        }
    }
}
