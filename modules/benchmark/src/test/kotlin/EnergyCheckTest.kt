package io.github.junekim0007.cryptobench.benchmark

import io.github.junekim0007.cryptobench.benchmark.check.EnergyCapability
import io.github.junekim0007.cryptobench.benchmark.check.PlanCheck
import io.github.junekim0007.cryptobench.benchmark.report.energy.EnergyWindows
import io.github.junekim0007.cryptobench.benchmark.report.MetricSamples
import io.github.junekim0007.cryptobench.preparation.global.EnergySettings
import io.github.junekim0007.cryptobench.preparation.global.HarnessSettings
import io.github.junekim0007.cryptobench.preparation.input.OperationInput
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyRecipe
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedRun
import org.junit.Assert.assertEquals
import org.junit.Test

class EnergyCheckTest {

    private val installed = { setOf("SUN") }

    private fun run(capture: String?, algorithm: String = "SHA-256") = PreparedRun(listOf(PreparedCase(
        BenchmarkCase("MessageDigest", algorithm, "SUN", Operation.DIGEST, inputSize = 64,
                      harness = HarnessSettings(energy = EnergySettings(capture = capture))),
        KeyRecipe.None, KeyMaterial.None, null, null, OperationInput.Message(ByteArray(64)),
    )), emptyList(), 1)

    private fun capability(responsive: Boolean, accept: Boolean = false, present: Boolean = true) =
        EnergyCapability(present, responsive, 1500.0, 1500.0, 2.0, accept)

    private fun reasons(capture: String?, capability: EnergyCapability?) =
        PlanCheck(installed) { capability }.check(run(capture)).map { it.reason.substringBefore(':') }

    @Test
    fun casesWithoutEnergyNeverAskForTheCapability() {
        assertEquals(emptyList<String>(), PlanCheck(installed) { error("must not be read") }.check(run(null)))
    }

    @Test
    fun energyCasesAreRefusedWithoutUsableRails() {
        assertEquals(listOf("energy_capability_unknown"), reasons("measured", null))
        assertEquals(listOf("no_power_rails"), reasons("dry", capability(responsive = false, present = false)))
        assertEquals(listOf("rails_unresponsive"), reasons("measured", capability(responsive = false)))
        assertEquals(emptyList<String>(), reasons("measured", capability(responsive = false, accept = true)))
        assertEquals(emptyList<String>(), reasons("dry", capability(responsive = true)))
    }

    @Test
    fun theCapabilityFileIsReadWhole() {
        val text = "schemaVersion: 1\nrailsPresent: true\nrailsResponsive: false\nidleMicrojoules: 30000\n" +
            "busyMicrojoules: 30000\nwindowSeconds: 2\nacceptUnresponsive: true\n"
        assertEquals(EnergyCapability(true, false, 30000.0, 30000.0, 2.0, true), EnergyCapability.parse(text))
    }

    @Test
    fun onlyMeasuredCasesBecomeAnEnergyMetric() {
        val text = """{"schemaVersion": 1, "cases": {
            "m": {"capture": "measured", "valid": true, "joulesPerOperation": 2.5e-6, "operations": 40000},
            "x": {"capture": "measured", "valid": false, "invalid": ["short_window"], "joulesPerOperation": -1, "operations": 9},
            "d": {"capture": "dry", "valid": true, "joulesPerOperation": 1.0e-6, "operations": 9}}}"""
        assertEquals(mapOf("m" to MetricSamples(listOf(2.5e-6), 40000)), EnergyWindows.measured(text))
        assertEquals(mapOf("x" to listOf("short_window")), EnergyWindows.invalid(text))
    }
}
