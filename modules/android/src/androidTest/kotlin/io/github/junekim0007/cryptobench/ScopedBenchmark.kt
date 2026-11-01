package io.github.junekim0007.cryptobench

import androidx.benchmark.BlackHole
import io.github.junekim0007.cryptobench.benchmark.run.CaseSettings
import io.github.junekim0007.cryptobench.preparation.global.GlobalReader
import io.github.junekim0007.cryptobench.preparation.inbound.InboundFile
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.junit.runners.Parameterized
import java.io.File

@RunWith(Parameterized::class)
class ScopedBenchmark(private val caseId: String, private val call: () -> Any?) {

    @get:Rule
    val benchmarkRule = JetpackRule(settings)

    @Test
    fun measure() {
        PinnedCase.run(caseId, settings) {
            benchmarkRule.measureRepeated {
                BlackHole.consume(call() ?: Unit)
            }
        }
    }

    companion object {

        // The run-level harness of the pushed effective.yaml, the settings every CryptoBenchmark case inherits.
        private val settings: CaseSettings by lazy {
            val global = GlobalReader.read(InboundFile.read(File(DevicePlan.directory, "effective.yaml")))
            CaseSettings.of(global.harness, global.metrics).also { settings -> JetpackConfig.refusal(settings)?.let { error(it) } }
        }

        @JvmStatic
        @Parameterized.Parameters(name = "{0}")
        fun cases(): List<Array<Any>> {
            val scopes = ScopeCatalog.load()
            val verdicts = scopes.map(ScopeCheck::of)
            ScopeInteropFile.write(DevicePlan.directory, verdicts)
            val measurable = verdicts.filter { it.measurable }.mapTo(HashSet()) { it.id }
            return scopes.filter { it.id in measurable }.flatMap { scope ->
                listOf(arrayOf<Any>("scope:${scope.id}:before", scope.before), arrayOf<Any>("scope:${scope.id}:after", scope.after))
            }
        }
    }
}
