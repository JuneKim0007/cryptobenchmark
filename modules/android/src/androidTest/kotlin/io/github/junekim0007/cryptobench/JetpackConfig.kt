package io.github.junekim0007.cryptobench

import androidx.benchmark.ExperimentalBenchmarkConfigApi
import androidx.benchmark.MicrobenchmarkConfig
import androidx.benchmark.ProfilerConfig
import io.github.junekim0007.cryptobench.benchmark.run.CaseSettings

@OptIn(ExperimentalBenchmarkConfigApi::class)
internal object JetpackConfig {

    fun of(settings: CaseSettings): MicrobenchmarkConfig = MicrobenchmarkConfig(
        profiler = when (settings.profiling) {
            CaseSettings.Profiling.NONE -> null
            CaseSettings.Profiling.METHOD_TRACING -> ProfilerConfig.MethodTracing()
            CaseSettings.Profiling.STACK_SAMPLING -> ProfilerConfig.StackSampling()
        },
        warmupCount = settings.warmupIterations,
        measurementCount = settings.iterations,
    )
}
