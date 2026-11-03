package io.github.junekim0007.cryptobench

import androidx.benchmark.ExperimentalBenchmarkConfigApi
import androidx.benchmark.MicrobenchmarkConfig
import androidx.benchmark.ProfilerConfig
import androidx.benchmark.TimeCapture
import androidx.test.platform.app.InstrumentationRegistry
import io.github.junekim0007.cryptobench.benchmark.run.CaseSettings
import io.github.junekim0007.cryptobench.settings.Metric

@OptIn(ExperimentalBenchmarkConfigApi::class)
internal object JetpackConfig {

    // Paired with scripts/device.py CPU_EVENTS.
    private const val CPU_EVENT_COUNTER = "androidx.benchmark.cpuEventCounter.enable"

    val METRICS: Set<Metric> = Metric.entries.toSet()

    // Default metrics: androidx adds its CPU event capture itself when the launch argument enabled it; an allocation pass adds its own.
    fun of(settings: CaseSettings): MicrobenchmarkConfig {
        val profiler = when (settings.profiling) {
            CaseSettings.Profiling.NONE -> null
            CaseSettings.Profiling.METHOD_TRACING -> ProfilerConfig.MethodTracing()
            CaseSettings.Profiling.STACK_SAMPLING -> ProfilerConfig.StackSampling()
        }
        if (PassArguments.countsAllocations) {
            return MicrobenchmarkConfig(metrics = listOf(TimeCapture(), SampledAllocations()), profiler = profiler,
                warmupCount = settings.warmupIterations, measurementCount = settings.iterations)
        }
        return MicrobenchmarkConfig(profiler = profiler, warmupCount = settings.warmupIterations, measurementCount = settings.iterations)
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
