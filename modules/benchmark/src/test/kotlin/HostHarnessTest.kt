package io.github.junekim0007.cryptobench.benchmark

import io.github.junekim0007.cryptobench.benchmark.run.CaseMeasurement
import io.github.junekim0007.cryptobench.benchmark.run.HostHarness
import io.github.junekim0007.cryptobench.preparation.global.HarnessSettings
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

    /** iterations is how many samples a case yields, not how many calls one sample makes. */
    @Test
    fun aCaseYieldsAsManySamplesAsTheHarnessSettingsAskFor() {
        assertEquals(3, quick.measure(digest(HarnessSettings())).nanosPerOperation.size)
        assertEquals(11, quick.measure(digest(HarnessSettings(iterations = 11))).nanosPerOperation.size)
    }

    /** The inner loop comes from the time budget, so a fast primitive is not measured against the clock's resolution. */
    @Test
    fun oneSampleLoopsUntilTheBudgetIsSpent() {
        val measurement = quick.measure(digest(HarnessSettings()))
        assertTrue("iterations ${measurement.iterations}", measurement.iterations > 1)
        assertTrue("median ${measurement.medianNanos}", measurement.medianNanos > 0)
    }

    /**
     * The progress line and the summary table must not disagree about one word: analyze.py takes the
     * mean of the two middle samples, and an even sample count is what processRepetitions produces.
     */
    @Test
    fun theMedianIsTheOneTheAnalysisComputes() {
        val case = digest(HarnessSettings()).case
        assertEquals(30L, CaseMeasurement(case, 1, listOf(10L, 50L, 20L, 40L)).medianNanos)
        assertEquals(20L, CaseMeasurement(case, 1, listOf(10L, 50L, 20L)).medianNanos)
    }
}
