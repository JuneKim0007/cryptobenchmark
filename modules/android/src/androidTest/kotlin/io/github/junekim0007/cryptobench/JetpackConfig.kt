package io.github.junekim0007.cryptobench

import android.annotation.SuppressLint
import androidx.benchmark.Arguments
import androidx.benchmark.ExperimentalBenchmarkConfigApi
import androidx.benchmark.MicrobenchmarkConfig
import androidx.benchmark.ProfilerConfig
import io.github.junekim0007.cryptobench.benchmark.run.CaseSettings
import io.github.junekim0007.cryptobench.settings.Metric

@OptIn(ExperimentalBenchmarkConfigApi::class)
internal object JetpackConfig {

    val METRICS: Set<Metric> = Metric.entries.toSet()

    // Default metrics: androidx adds its CPU event capture itself when the launch argument enabled it.
    fun of(settings: CaseSettings): MicrobenchmarkConfig = MicrobenchmarkConfig(
        profiler = when (settings.profiling) {
            CaseSettings.Profiling.NONE -> null
            CaseSettings.Profiling.METHOD_TRACING -> ProfilerConfig.MethodTracing()
            CaseSettings.Profiling.STACK_SAMPLING -> ProfilerConfig.StackSampling()
        },
        warmupCount = settings.warmupIterations,
        measurementCount = settings.iterations,
    )

    fun timingOnly(settings: CaseSettings): Boolean = Metric.ALLOCATION !in settings.metrics

    fun refusal(settings: CaseSettings): String? =
        if (timingOnly(settings) && settings.profiling != CaseSettings.Profiling.NONE)
            "not_supported: profiling ${settings.profiling} needs ALLOCATION in run.metrics; androidx's timing-only mode has no profiled phase"
        else null

    // The counter is a launch argument, so it is checked when a case runs, not when the plan is prepared.
    @SuppressLint("RestrictedApi")
    fun counterMismatch(settings: CaseSettings): String? {
        val counting = Arguments.cpuEventCounterEnable
        return when {
            Metric.CPU_EVENTS in settings.metrics && !counting ->
                "not_supported: CPU_EVENTS, androidx did not enable its CPU event counter (launch argument androidx.benchmark.cpuEventCounter.enable, rooted device)"
            Metric.CPU_EVENTS !in settings.metrics && counting ->
                "not_requested: androidx counts CPU events but run.metrics has no CPU_EVENTS"
            else -> null
        }
    }
}
