package io.github.junekim0007.cryptobench.benchmark

import io.github.junekim0007.cryptobench.benchmark.report.MetricSamples
import io.github.junekim0007.cryptobench.benchmark.run.CaseMeasurement
import io.github.junekim0007.cryptobench.benchmark.run.HostHarness
import io.github.junekim0007.cryptobench.settings.HarnessSettings
import io.github.junekim0007.cryptobench.preparation.input.InputBytes
import io.github.junekim0007.cryptobench.preparation.input.OperationInput
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyRecipe
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class HostHarnessTest {

    private fun digest(harness: HarnessSettings) = PreparedCase(
        BenchmarkCase("MessageDigest", "SHA-256", "SUN", Operation.DIGEST, inputSize = 64, harness = harness),
        KeyRecipe.None,
        KeyMaterial.None,
        null,
        null,
        OperationInput.Message(InputBytes.of(7, 64)),
    )

    private val quick = HostHarness(warmupNanos = 2_000_000L, runNanos = 1_000_000L, runs = 3)

    @Test
    fun aCaseYieldsAsManySamplesAsTheHarnessSettingsAskFor() {
        assertEquals(3, quick.measure(digest(HarnessSettings())).nanosPerOperation.size)
        assertEquals(11, quick.measure(digest(HarnessSettings(iterations = 11))).nanosPerOperation.size)
    }

    @Test
    fun oneSampleLoopsUntilTheBudgetIsSpent() {
        val measurement = quick.measure(digest(HarnessSettings()))
        assertTrue("iterations ${measurement.iterations}", measurement.iterations > 1)
        assertTrue("median ${measurement.medianNanos}", measurement.medianNanos > 0)
    }

    @Test
    fun theHostRowCarriesOnlyWhatTheHostCanMeasure() {
        val row = quick.measure(digest(HarnessSettings())).row()
        assertEquals(listOf(MetricSamples.TIME), row.metrics.keys.toList())
    }

    @Test
    fun theMedianIsTheOneTheAnalysisComputes() {
        val case = digest(HarnessSettings()).case
        assertEquals(30.0, CaseMeasurement(case, "none", 1, listOf(10.0, 50.0, 20.0, 40.0)).medianNanos, 0.0)
        assertEquals(20.0, CaseMeasurement(case, "none", 1, listOf(10.0, 50.0, 20.0)).medianNanos, 0.0)
    }
}
