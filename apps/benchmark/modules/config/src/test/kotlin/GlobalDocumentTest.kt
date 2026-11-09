package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.config.effective.EffectiveBuilder
import io.github.junekim0007.cryptobench.config.effective.EffectiveDocument
import io.github.junekim0007.cryptobench.config.global.GlobalDocument
import io.github.junekim0007.cryptobench.config.global.dto.AnalysisSettings
import io.github.junekim0007.cryptobench.config.global.dto.BundledProvider
import io.github.junekim0007.cryptobench.config.global.dto.MeasurePass
import io.github.junekim0007.cryptobench.config.global.dto.ThermalGate
import io.github.junekim0007.cryptobench.config.global.dto.Warmup
import io.github.junekim0007.cryptobench.config.yaml.YamlCodec
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test

/** What global.yaml reads: the defaults that change what a run measures, its refusals, and the path to the effective file. */
class GlobalDocumentTest {

    private val fixture = DocumentFixture()
    private val codec = fixture.codec
    private val inventory = fixture.inventory
    private val testSet = fixture.testSet

    private val head = "schemaVersion: 1\nselection: {testSet: testsets/scope.yaml}\n"

    private fun global(text: String) = GlobalDocument.parse(codec.load(head + text))

    private fun run(text: String) = global(text).run

    private fun effective(chosen: io.github.junekim0007.cryptobench.config.global.dto.GlobalConfig) = EffectiveDocument.parse(codec.load(YamlCodec().dump(EffectiveDocument.of(
        EffectiveBuilder().build(chosen, testSet, inventory, EffectiveBuilder.Files("global.yaml", "testsets/scope.yaml", "inventory.yaml"))))))

    @Test
    fun aMissingRunSectionOrKeyKeepsDefaults() {
        assertEquals(listOf(1024), run("").inputSizes)
        val partial = run("run: {processRepetitions: 3}\n")
        assertEquals(3, partial.processRepetitions)
        assertEquals(listOf(1024), partial.inputSizes)
    }

    /** A changed default changes every number of a later run without a config change. */
    @Test
    fun whatARunMeasuresWhenNothingIsSaid() {
        val run = run("")
        assertEquals("case", run.isolation)
        assertEquals(null, run.thermalGate)
        assertEquals(listOf("fixed", "notFixed"), run.variants)
        assertEquals(Warmup(10, emptyList()), run.warmup)
        assertEquals(emptyList<MeasurePass>(), run.passes)
    }

    @Test
    fun everyRunSettingSurvivesTheFile() {
        val written = run("""
            run:
              isolation: run
              metrics: [TIME, ALLOCATION]
              variants: [notFixed]
              thermalThrottleSleepSeconds: 30
              caseCooldownSeconds: 20
              warmup: {iterations: 0, jobs: [{type: MessageDigest, name: SHA-256}]}
              passes: {timing: {samples: 3}, allocation: {samples: 2}}
        """.trimIndent() + "\n")
        assertEquals(listOf(MeasurePass("timing", 3), MeasurePass("allocation", 2)), written.passes)
        assertEquals(written, GlobalDocument.parse(codec.load(YamlCodec().dump(GlobalDocument.of(global("").copy(run = written))))).run)
    }

    @Test
    fun aGateCanBeWrittenAndSwitchedOff() {
        val written = run("run: {thermalGate: {temperatureKeptCelsius: 36.0}}\n")
        assertEquals(ThermalGate(36.0), written.thermalGate)
        assertEquals(written, GlobalDocument.parse(codec.load(YamlCodec().dump(GlobalDocument.of(global("").copy(run = written))))).run)
        assertEquals(null, run("run: {}\n").thermalGate)
    }

    @Test
    fun aBadRunSettingIsRefusedByItsCode() {
        listOf(
            "run: {isolation: process}\n" to "invalid: run.isolation",
            "run: {thermalThrottleSleepSeconds: -1}\n" to "negative: thermalThrottleSleepSeconds",
            "run: {caseCooldownSeconds: -1}\n" to "negative: caseCooldownSeconds",
            "run: {warmup: {iterations: -1}}\n" to "negative: run.warmup.iterations",
            "run: {thermalGate: {}}\n" to "missing_field: run.thermalGate.temperatureKeptCelsius",
            "run: {thermalGate: {temperatureKeptCelsius: 36.0, cooldownMinutes: 1.5}}\n" to "not_whole: run.thermalGate.cooldownMinutes",
            "run: {thermalGate: {temperatureKeptCelsius: 36.0, pollMinutes: 0}}\n" to "not_positive: run.thermalGate.pollMinutes",
            "run: {thermalGate: {temperatureKeptCelsius: 36.0, onDiscardLimit: nope}}\n" to "invalid: run.thermalGate.onDiscardLimit",
            "run: {thermalGate: {temperatureKeptCelsius: 36.0, margin: 3}}\n" to "unknown_keys: run.thermalGate [margin]",
            "run: {isolation: run, thermalGate: {temperatureKeptCelsius: 36.0}}\n" to "invalid: run.thermalGate needs run.isolation",
            "run: {variants: []}\n" to "invalid: run.variants",
            "run: {variants: [fixed, fixed]}\n" to "invalid: run.variants",
            "run: {passes: {timing: {samples: 1}, speed: {samples: 1}}}\n" to "invalid: run.passes.speed",
            "run: {passes: {timing: {samples: 0}}}\n" to "not_positive: run.passes.timing.samples",
            "run: {passes: {energy: {samples: 5}}}\n" to "missing_pass: run.passes [energy]",
            "run: {passes: {timing: {samples: 1}, allocation: {samples: 1}}}\n" to "pass_without_metric: run.passes.allocation",
        ).forEach { (text, code) ->
            val message = assertThrows(text, IllegalArgumentException::class.java) { run(text) }.message!!
            assertTrue(message, message.startsWith(code))
        }
    }

    /** No charts line means every chart; naming some turns the rest off; an empty list writes the summary only. */
    @Test
    fun theChartListDefaultsToAllAndNamingSomeTurnsTheRestOff() {
        assertEquals(AnalysisSettings.Chart.entries.toList(), global("").analysis.charts)
        assertEquals(listOf(AnalysisSettings.Chart.IQR_BARS, AnalysisSettings.Chart.STABILITY), global("analysis: {charts: [iqrBars, stability]}\n").analysis.charts)
        assertEquals(emptyList<AnalysisSettings.Chart>(), global("analysis: {charts: []}\n").analysis.charts)
    }

    /** The statistic, units and folder are frozen into effective.yaml, where the tools read them. */
    @Test
    fun theAnalysisChoiceTravelsToTheEffectiveFile() {
        val chosen = GlobalDocument.parse(codec.load(Fixtures.GLOBAL +
            "analysis: {statistic: {headline: MEDIAN, meanUpToCovPercent: 2.5}, units: {latency: us, throughput: ops/s}, dir: out/charts/<run-id>}\n"))
        assertEquals(AnalysisSettings.Headline.MEDIAN, chosen.analysis.statistic.headline)
        assertEquals(AnalysisSettings.Units(AnalysisSettings.LatencyUnit.US, AnalysisSettings.ThroughputUnit.OPS_PER_SECOND), chosen.analysis.units)
        assertEquals(chosen.analysis, effective(chosen).analysis)
    }

    /** A bundled provider list is optional; written, it travels unchanged to effective.yaml for the build and the device. */
    @Test
    fun bundledProvidersAreOptionalAndTravelToTheEffectiveFile() {
        assertEquals(emptyList<BundledProvider>(), GlobalDocument.parse(codec.load(Fixtures.GLOBAL)).providers.bundled)
        val bundled = GlobalDocument.parse(codec.load(Fixtures.GLOBAL + "providers:\n  bundled:\n  - {artifact: 'g:n:1', create: 'a.b.P#newProvider', alias: P2}\n  - {artifact: 'h:m:2', create: a.b.Q}\n"))
        assertEquals(listOf(BundledProvider("g:n:1", "a.b.P#newProvider", "P2"), BundledProvider("h:m:2", "a.b.Q")), bundled.providers.bundled)
        assertEquals(bundled.providers.bundled, effective(bundled).bundledProviders)
    }
}
