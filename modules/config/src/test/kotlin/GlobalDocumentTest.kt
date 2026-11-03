package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.config.effective.EffectiveBuilder
import io.github.junekim0007.cryptobench.config.effective.EffectiveDocument
import io.github.junekim0007.cryptobench.config.global.GlobalDocument
import io.github.junekim0007.cryptobench.config.global.dto.AnalysisSettings
import io.github.junekim0007.cryptobench.config.global.dto.BundledProvider
import io.github.junekim0007.cryptobench.config.global.dto.MeasurePass
import io.github.junekim0007.cryptobench.config.yaml.YamlCodec
import java.nio.file.Files
import org.junit.Assert.assertEquals
import org.junit.Test

/** What global.yaml reads: defaults when a section or key is missing, the analysis settings, and their path to the effective file. */
class GlobalDocumentTest {

    private val fixture = DocumentFixture()
    private val files = fixture.files
    private val codec = fixture.codec
    private val directory = fixture.directory
    private val inventory = fixture.inventory
    private val global = fixture.global
    private val testSet = fixture.testSet
    private val effective = fixture.effective

    @Test
    fun aMissingRunSectionOrKeyKeepsDefaults() {
        val minimal = GlobalDocument.parse(codec.load("schemaVersion: 1\nselection: {testSet: testsets/all.yaml}\n"))
        assertEquals(listOf(1024), minimal.run.inputSizes)
        val partial = GlobalDocument.parse(codec.load("schemaVersion: 1\nselection: {testSet: testsets/all.yaml}\nrun: {processRepetitions: 3}\n"))
        assertEquals(3, partial.run.processRepetitions)
        assertEquals(listOf(1024), partial.run.inputSizes)
    }

    @Test
    fun isolationDefaultsToOneProcessPerCaseAndRefusesAnythingButCaseOrRun() {
        fun run(text: String) = GlobalDocument.parse(codec.load("schemaVersion: 1\nselection: {testSet: testsets/all.yaml}\n$text")).run
        assertEquals("case", run("").isolation)
        assertEquals("run", run("run: {isolation: run}\n").isolation)
        val refused = org.junit.Assert.assertThrows(IllegalArgumentException::class.java) { run("run: {isolation: process}\n") }
        assertEquals("invalid: run.isolation process, expected one of [case, run]", refused.message)
    }

    @Test
    fun theThrottleSleepIsUnsetUnlessWrittenAndTravelsToTheEffectiveFile() {
        fun run(text: String) = GlobalDocument.parse(codec.load("schemaVersion: 1\nselection: {testSet: testsets/all.yaml}\n$text")).run
        assertEquals(null, run("").thermalThrottleSleepSeconds)
        assertEquals(30, run("run: {thermalThrottleSleepSeconds: 30}\n").thermalThrottleSleepSeconds)
        assertEquals(false, "thermalThrottleSleepSeconds" in io.github.junekim0007.cryptobench.config.global.RunDocument.of(run("")))
        val refused = org.junit.Assert.assertThrows(IllegalArgumentException::class.java) { run("run: {thermalThrottleSleepSeconds: -1}\n") }
        assertEquals("negative: thermalThrottleSleepSeconds -1", refused.message)
    }

    @Test
    fun theWarmupDefaultsToTenIterationsOfThePlansFirstCasesAndZeroTurnsItOff() {
        fun run(text: String) = GlobalDocument.parse(codec.load("schemaVersion: 1\nselection: {testSet: testsets/all.yaml}\n$text")).run
        assertEquals(io.github.junekim0007.cryptobench.config.global.dto.Warmup(10, emptyList()), run("").warmup)
        val chosen = run("run: {warmup: {iterations: 0, jobs: [{type: MessageDigest, name: SHA-256}]}}\n").warmup
        assertEquals(0, chosen.iterations)
        assertEquals("SHA-256", chosen.jobs.single().name)
        val refused = org.junit.Assert.assertThrows(IllegalArgumentException::class.java) { run("run: {warmup: {iterations: -1}}\n") }
        assertEquals("negative: run.warmup.iterations -1", refused.message)
    }

    @Test
    fun theCaseCooldownIsOffByDefaultAndTravelsToTheEffectiveFile() {
        fun run(text: String) = GlobalDocument.parse(codec.load("schemaVersion: 1\nselection: {testSet: testsets/all.yaml}\n$text")).run
        assertEquals(0, run("").caseCooldownSeconds)
        assertEquals(20, io.github.junekim0007.cryptobench.config.global.RunDocument.of(run("run: {caseCooldownSeconds: 20}\n"))["caseCooldownSeconds"])
        val refused = org.junit.Assert.assertThrows(IllegalArgumentException::class.java) { run("run: {caseCooldownSeconds: -1}\n") }
        assertEquals("negative: caseCooldownSeconds -1", refused.message)
    }

    @Test
    fun theThermalGateIsOffUnlessWrittenNamesItsSensorsAndTravelsToTheEffectiveFile() {
        fun run(text: String) = GlobalDocument.parse(codec.load("schemaVersion: 1\nselection: {testSet: testsets/all.yaml}\n$text")).run
        assertEquals(null, run("").thermalGate)
        assertEquals(false, "thermalGate" in io.github.junekim0007.cryptobench.config.global.RunDocument.of(run("")))
        val gate = run("run: {thermalGate: {sensors: [s1, s2]}}\n").thermalGate!!
        assertEquals(io.github.junekim0007.cryptobench.config.global.dto.ThermalGate(true, listOf("s1", "s2"), 3.0, 5, 300), gate)
        assertEquals(mapOf("enabled" to true, "sensors" to listOf("s1", "s2"), "marginCelsius" to 3.0, "pollSeconds" to 5, "timeoutSeconds" to 300),
            io.github.junekim0007.cryptobench.config.global.RunDocument.of(run("run: {thermalGate: {sensors: [s1, s2]}}\n"))["thermalGate"])
        assertEquals(false, run("run: {thermalGate: {enabled: false}}\n").thermalGate!!.enabled)
        listOf(
            "run: {thermalGate: {}}\n" to "missing_field: run.thermalGate.sensors, the device's sensor names to gate on",
            "run: {thermalGate: {sensors: [s], marginCelsius: -1}}\n" to "negative: run.thermalGate.marginCelsius -1.0",
            "run: {thermalGate: {sensors: [s], pollSeconds: 0}}\n" to "not_positive: run.thermalGate.pollSeconds 0",
            "run: {thermalGate: {sensors: [s], timeoutSeconds: -5}}\n" to "negative: run.thermalGate.timeoutSeconds -5",
            "run: {thermalGate: {sensors: [s], margin: 3}}\n" to "unknown_keys: run.thermalGate [margin], known [enabled, sensors, marginCelsius, pollSeconds, timeoutSeconds]",
        ).forEach { (text, message) ->
            assertEquals(message, org.junit.Assert.assertThrows(IllegalArgumentException::class.java) { run(text) }.message)
        }
    }

    @Test
    fun scopedRepetitionsDefaultToThreeAndRefuseZero() {
        fun run(text: String) = GlobalDocument.parse(codec.load("schemaVersion: 1\nselection: {testSet: testsets/all.yaml}\n$text")).run
        assertEquals(3, run("").scopedRepetitions)
        assertEquals(4, run("run: {scopedRepetitions: 4}\n").scopedRepetitions)
        val refused = org.junit.Assert.assertThrows(IllegalArgumentException::class.java) { run("run: {scopedRepetitions: 0}\n") }
        assertEquals("not_positive: scopedRepetitions 0", refused.message)
    }

    @Test
    fun passesAreReadInTheirOrderAndRefuseWhatNoPassCanMeasure() {
        fun run(text: String) = GlobalDocument.parse(codec.load("schemaVersion: 1\nselection: {testSet: testsets/all.yaml}\n$text")).run
        assertEquals(emptyList<MeasurePass>(), run("").passes)
        val three = run("run: {metrics: [TIME, ALLOCATION], passes: {timing: {samples: 300}, energy: {samples: 100}, allocation: {samples: 100}}}\n")
        assertEquals(listOf(MeasurePass("timing", 300), MeasurePass("energy", 100), MeasurePass("allocation", 100)), three.passes)
        val reread = GlobalDocument.parse(codec.load(YamlCodec().dump(GlobalDocument.of(GlobalDocument.parse(codec.load(
            "schemaVersion: 1\nselection: {testSet: testsets/all.yaml}\nrun: {metrics: [TIME, ALLOCATION], passes: {timing: {samples: 3}, allocation: {samples: 2}}}\n"))))))
        assertEquals(listOf(MeasurePass("timing", 3), MeasurePass("allocation", 2)), reread.run.passes)
        fun refused(text: String) = org.junit.Assert.assertThrows(IllegalArgumentException::class.java) { run(text) }.message
        assertEquals("invalid: run.passes.speed, known [timing, energy, allocation]", refused("run: {passes: {timing: {samples: 1}, speed: {samples: 1}}}\n"))
        assertEquals("not_positive: run.passes.timing.samples 0", refused("run: {passes: {timing: {samples: 0}}}\n"))
        assertEquals("missing_pass: run.passes [energy], timing is the pass every other merges into", refused("run: {passes: {energy: {samples: 5}}}\n"))
        assertEquals("pass_without_metric: run.passes.allocation measures ALLOCATION, which run.metrics [TIME] does not report",
            refused("run: {passes: {timing: {samples: 1}, allocation: {samples: 1}}}\n"))
    }

    /** The statistic that leads is the user's call; auto at 5% when nothing is said, and the choice is frozen into effective.yaml. */
    @Test
    fun theHeadlineStatisticDefaultsToAutoAndTravelsToTheEffectiveFile() {
        val minimal = GlobalDocument.parse(codec.load("schemaVersion: 1\nselection: {testSet: testsets/all.yaml}\n"))
        assertEquals(AnalysisSettings.Headline.AUTO, minimal.analysis.statistic.headline)
        assertEquals(5.0, minimal.analysis.statistic.meanUpToCovPercent, 0.0)

        val chosen = GlobalDocument.parse(codec.load(Fixtures.GLOBAL + "analysis: {statistic: {headline: MEDIAN, meanUpToCovPercent: 2.5}}\n"))
        assertEquals(AnalysisSettings.Headline.MEDIAN, chosen.analysis.statistic.headline)
        val built = EffectiveBuilder().build(chosen, testSet, inventory, EffectiveBuilder.Files("global.yaml", "testsets/scope.yaml", "inventory.yaml"))
        val reread = EffectiveDocument.parse(codec.load(YamlCodec().dump(EffectiveDocument.of(built))))
        assertEquals(chosen.analysis, reread.analysis)
    }

    /** No charts line means every chart; naming some turns the rest off; an empty list writes the summary only. */
    @Test
    fun theChartListDefaultsToAllAndNamingSomeTurnsTheRestOff() {
        val all = AnalysisSettings.Chart.entries.toList()
        assertEquals(all, GlobalDocument.parse(codec.load("schemaVersion: 1\nselection: {testSet: a.yaml}\n")).analysis.charts)
        assertEquals(null, GlobalDocument.parse(codec.load("schemaVersion: 1\nselection: {testSet: a.yaml}\n")).analysis.dir)
        val some = GlobalDocument.parse(codec.load("schemaVersion: 1\nselection: {testSet: a.yaml}\nanalysis: {charts: [iqrBars, stability], dir: out/charts/<run-id>}\n")).analysis
        assertEquals(listOf(AnalysisSettings.Chart.IQR_BARS, AnalysisSettings.Chart.STABILITY), some.charts)
        assertEquals("out/charts/<run-id>", some.dir)
        assertEquals(emptyList<AnalysisSettings.Chart>(), GlobalDocument.parse(codec.load("schemaVersion: 1\nselection: {testSet: a.yaml}\nanalysis: {charts: []}\n")).analysis.charts)
    }

    /** Display units default to ms and MB/s; a choice travels to the effective file, where the tools read it. */
    @Test
    fun theDisplayUnitsDefaultToMsAndMbPerSecondAndTravelToTheEffectiveFile() {
        val minimal = GlobalDocument.parse(codec.load("schemaVersion: 1\nselection: {testSet: a.yaml}\n"))
        assertEquals(AnalysisSettings.Units(AnalysisSettings.LatencyUnit.MS, AnalysisSettings.ThroughputUnit.MB_PER_SECOND), minimal.analysis.units)
        val chosen = GlobalDocument.parse(codec.load(Fixtures.GLOBAL + "analysis: {units: {latency: us, throughput: ops/s}}\n"))
        assertEquals(AnalysisSettings.Units(AnalysisSettings.LatencyUnit.US, AnalysisSettings.ThroughputUnit.OPS_PER_SECOND), chosen.analysis.units)
        val built = EffectiveBuilder().build(chosen, testSet, inventory, EffectiveBuilder.Files("global.yaml", "testsets/scope.yaml", "inventory.yaml"))
        val reread = EffectiveDocument.parse(codec.load(YamlCodec().dump(EffectiveDocument.of(built))))
        assertEquals(chosen.analysis.units, reread.analysis.units)
    }

    /** A bundled provider list is optional; written, it travels unchanged to effective.yaml for the build and the device. */
    @Test
    fun bundledProvidersAreOptionalAndTravelToTheEffectiveFile() {
        assertEquals(emptyList<BundledProvider>(), GlobalDocument.parse(codec.load(Fixtures.GLOBAL)).providers.bundled)

        val bundled = GlobalDocument.parse(codec.load(Fixtures.GLOBAL + "providers:\n  bundled:\n  - {artifact: 'g:n:1', create: 'a.b.P#newProvider', alias: P2}\n  - {artifact: 'h:m:2', create: a.b.Q}\n"))
        assertEquals(listOf(BundledProvider("g:n:1", "a.b.P#newProvider", "P2"), BundledProvider("h:m:2", "a.b.Q")), bundled.providers.bundled)
        assertEquals(bundled, GlobalDocument.parse(codec.load(YamlCodec().dump(GlobalDocument.of(bundled)))))
        val built = EffectiveBuilder().build(bundled, testSet, inventory, EffectiveBuilder.Files("global.yaml", "testsets/scope.yaml", "inventory.yaml"))
        val written = EffectiveDocument.of(built)
        assertEquals(listOf(mapOf("artifact" to "g:n:1", "create" to "a.b.P#newProvider", "alias" to "P2"), mapOf("artifact" to "h:m:2", "create" to "a.b.Q")), written["bundledProviders"])
        assertEquals(bundled.providers.bundled, EffectiveDocument.parse(codec.load(YamlCodec().dump(written))).bundledProviders)
        assertEquals(null, EffectiveDocument.of(EffectiveBuilder().build(GlobalDocument.parse(codec.load(Fixtures.GLOBAL)), testSet, inventory, EffectiveBuilder.Files("g", "t", "i")))["bundledProviders"])
    }
}
