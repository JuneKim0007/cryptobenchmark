package io.github.junekim0007.cryptobench.benchmark

import io.github.junekim0007.cryptobench.benchmark.run.HostHarness
import io.github.junekim0007.cryptobench.preparation.input.InputBytes
import io.github.junekim0007.cryptobench.preparation.input.OperationInput
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyRecipe
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import io.github.junekim0007.cryptobench.settings.CpuSettings
import io.github.junekim0007.cryptobench.settings.HarnessSettings
import org.junit.Assert.assertEquals
import org.junit.Test

/** Characterization: the host harness reads only harness.iterations; the other harness keys change nothing it samples. */
class HostHarnessSettingsTest {

    private val quick = HostHarness(warmupNanos = 1_000_000L, runNanos = 500_000L, runs = 3, collectionCount = { 0L })

    private fun samples(harness: HarnessSettings): Int = quick.measure(PreparedCase(
        BenchmarkCase("MessageDigest", "SHA-256", "SUN", Operation.DIGEST, inputSize = 64, harness = harness),
        KeyRecipe.None, KeyMaterial.None, null, null, OperationInput.Message(InputBytes.of(7, 64)),
    )).time.runs.size

    @Test
    fun todayHostIgnoresWarmupIterationsCpuAndProfiling() {
        val ignored = HarnessSettings(warmupIterations = 50, profiling = "MethodTracing", cpu = CpuSettings("0", true))
        assertEquals(listOf(3, 3, 4, 4), listOf(
            samples(HarnessSettings()), samples(ignored), samples(HarnessSettings(iterations = 4)), samples(ignored.copy(iterations = 4)),
        ))
    }
}
