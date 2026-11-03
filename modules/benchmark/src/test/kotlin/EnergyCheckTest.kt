package io.github.junekim0007.cryptobench.benchmark

import io.github.junekim0007.cryptobench.benchmark.check.EnergyCapability
import io.github.junekim0007.cryptobench.benchmark.check.PlanCheck
import io.github.junekim0007.cryptobench.benchmark.run.HostHarness
import io.github.junekim0007.cryptobench.benchmark.report.energy.EnergyWindows
import io.github.junekim0007.cryptobench.benchmark.report.BenchmarkJson
import io.github.junekim0007.cryptobench.benchmark.report.Merge
import io.github.junekim0007.cryptobench.benchmark.report.MetricSamples
import io.github.junekim0007.cryptobench.benchmark.report.ResultRow
import io.github.junekim0007.cryptobench.settings.EnergySettings
import io.github.junekim0007.cryptobench.settings.HarnessSettings
import io.github.junekim0007.cryptobench.preparation.input.OperationInput
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyRecipe
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedRun
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

class EnergyCheckTest {

    private val installed = { setOf("SUN") }

    private fun run(capture: String?, algorithm: String = "SHA-256", source: String? = null) = PreparedRun(listOf(PreparedCase(
        BenchmarkCase("MessageDigest", algorithm, "SUN", Operation.DIGEST, inputSize = 64,
                      harness = HarnessSettings(energy = EnergySettings(capture = capture, source = source))),
        KeyRecipe.None, KeyMaterial.None, null, null, OperationInput.Message(ByteArray(64)),
    )), emptyList(), 1)

    private fun capability(responsive: Boolean, accept: Boolean = false, present: Boolean = true) =
        EnergyCapability(present, responsive, 1500.0, 1500.0, 2.0, accept)

    private fun reasons(capture: String?, capability: EnergyCapability?) =
        PlanCheck(HostHarness.METRICS, installed) { capability }.check(run(capture)).map { it.reason.substringBefore(':') }

    @Test
    fun casesWithoutEnergyNeverAskForTheCapability() {
        assertEquals(emptyList<String>(), PlanCheck(HostHarness.METRICS, installed) { error("must not be read") }.check(run(null)))
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
    fun aSourceWithoutRailsNeverReadsTheRailCapability() {
        val check = PlanCheck(HostHarness.METRICS, installed) { error("must not be read") }
        assertEquals(emptyList<String>(), check.check(run("measured", source = "manafa")).map { it.reason })
        assertEquals(listOf("no_power_rails"), PlanCheck(HostHarness.METRICS, installed) { capability(responsive = false, present = false) }
            .check(run("measured", source = "rails")).map { it.reason.substringBefore(':') })
    }

    @Test
    fun theCapabilityFileIsReadWhole() {
        val text = "schemaVersion: 1\nrailsPresent: true\nrailsResponsive: false\nidleMicrojoules: 30000\n" +
            "busyMicrojoules: 30000\nwindowSeconds: 2\nacceptUnresponsive: true\n"
        assertEquals(EnergyCapability(true, false, 30000.0, 30000.0, 2.0, true), EnergyCapability.parse(text))
    }

    @Test
    fun anEnergyFileWithoutItsSchemaOrKindIsRefused() {
        fun failure(text: String) = assertThrows(IllegalArgumentException::class.java) { EnergyWindows.read(text) }.message
        assertEquals("unsupported: energy.json schemaVersion 1", failure("""{"schemaVersion": 1, "cases": {}}"""))
        assertEquals("missing_field: energy.json kind", failure("""{"schemaVersion": 2, "source": "rails", "cases": {}}"""))
    }

    @Test
    fun sourceAndKindSurviveTheFileAndAMergeOfProcesses() {
        val energy = MetricSamples(listOf(1.5), 10, source = "manafa", kind = "estimated")
        fun row(samples: MetricSamples) = ResultRow("c", "T", "A", "P", "OP", null, null, null,
                                                    mapOf(MetricSamples.TIME to MetricSamples(listOf(9.0), 1), MetricSamples.ENERGY to samples), emptyMap())
        val text = BenchmarkJson(File(".")).text(emptyMap(), listOf(row(energy)))
        assertTrue(text, text.contains(""""energyJ": {"iterations": 10, "runs": [1.5], "source": "manafa", "kind": "estimated"}"""))
        val merged = Merge.merge(listOf(text, text)).rows.single().metrics.getValue(MetricSamples.ENERGY)
        assertEquals(listOf(1.5, 1.5), merged.runs)
        assertEquals("manafa" to "estimated", merged.source to merged.kind)
        val measured = energy.copy(source = "rails", kind = "measured")
        val other = BenchmarkJson(File(".")).text(emptyMap(), listOf(row(measured)))
        val refused = Merge.merge(listOf(text, other))
        assertEquals(listOf("not_merged: c: energy_kinds_differ: estimated and measured"), refused.dropped)
        assertEquals(emptyList<String>(), refused.rows.map { it.id })
    }

    @Test
    fun onlyMeasuredCasesBecomeAnEnergyMetric() {
        val text = """{"schemaVersion": 2, "source": "manafa", "kind": "estimated", "cases": {
            "m": {"capture": "measured", "valid": true, "joulesPerOperation": 2.5e-6, "operations": 40000},
            "x": {"capture": "measured", "valid": false, "invalid": ["short_window"], "joulesPerOperation": -1, "operations": 9},
            "d": {"capture": "dry", "valid": true, "joulesPerOperation": 1.0e-6, "operations": 9}}}"""
        val read = EnergyWindows.read(text)
        assertEquals(mapOf("m" to MetricSamples(listOf(2.5e-6), 40000, source = "manafa", kind = "estimated")), read.samples)
        assertEquals(mapOf("x" to listOf("short_window")), read.notJoined)
    }

    @Test
    fun aValidCaseWithoutANumberIsNotJoinedAndTheOthersAre() {
        val text = """{"schemaVersion": 2, "source": "rails", "kind": "measured", "cases": {
            "m": {"capture": "measured", "valid": true, "joulesPerOperation": 2.5e-6, "operations": 4},
            "none": {"capture": "measured", "valid": true, "joulesPerOperation": null, "operations": 0},
            "zero": {"capture": "measured", "valid": true, "joulesPerOperation": 1.0, "operations": 0},
            "empty": {"capture": "measured", "valid": false, "invalid": []}}}"""
        val read = EnergyWindows.read(text)
        assertEquals(setOf("m"), read.samples.keys)
        assertEquals(mapOf("none" to listOf("missing_field: joulesPerOperation"), "zero" to listOf("out_of_range: operations 0"),
                           "empty" to listOf("unjudged")), read.notJoined)
    }
}
