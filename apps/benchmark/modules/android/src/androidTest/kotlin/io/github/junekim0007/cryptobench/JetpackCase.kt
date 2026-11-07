package io.github.junekim0007.cryptobench

import androidx.benchmark.BlackHole
import androidx.benchmark.ExperimentalBenchmarkConfigApi
import androidx.benchmark.junit4.BenchmarkRule
import androidx.benchmark.junit4.measureRepeated
import io.github.junekim0007.cryptobench.benchmark.run.CaseSettings
import io.github.junekim0007.cryptobench.benchmark.run.OutputHook
import io.github.junekim0007.cryptobench.preparation.operation.Invocation
import org.junit.Rule

/** One Jetpack-timed case: its rule from the case settings, the counter check, the pin, and the timed loop over one call. */
@OptIn(ExperimentalBenchmarkConfigApi::class)
abstract class JetpackCase(private val caseId: String, caseSettings: CaseSettings) {

    protected val settings: CaseSettings = PassArguments.applied(caseSettings)

    @get:Rule
    val benchmarkRule = BenchmarkRule(JetpackConfig.of(settings))

    protected fun timed(prepare: () -> () -> Any?) {
        JetpackConfig.counterMismatch(settings)?.let { error(it) }
        val call = prepare()
        PinnedCase.run(caseId, settings) {
            benchmarkRule.measureRepeated {
                // Unit stands in for null: the call returns Any? and BlackHole.consume takes Any.
                BlackHole.consume(call() ?: Unit)
            }
        }
    }

    // Check mode: under androidx's dry run the block runs once; its output goes to the hook, never to a BlackHole.
    protected fun once(invocation: Invocation, hook: OutputHook) {
        benchmarkRule.measureRepeated { hook.consume(invocation.once()) }
    }
}
