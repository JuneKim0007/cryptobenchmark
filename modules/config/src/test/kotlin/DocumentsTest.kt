package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.config.effective.EffectiveBuilder
import io.github.junekim0007.cryptobench.config.effective.EffectiveDocument
import io.github.junekim0007.cryptobench.config.global.GlobalDocument
import io.github.junekim0007.cryptobench.config.global.dto.AnalysisSettings
import io.github.junekim0007.cryptobench.config.inventory.InventoryBuilder
import io.github.junekim0007.cryptobench.config.inventory.InventoryDocument
import io.github.junekim0007.cryptobench.config.source.CaptureSource
import io.github.junekim0007.cryptobench.config.source.TrialSource
import io.github.junekim0007.cryptobench.config.testset.TestSetDocument
import io.github.junekim0007.cryptobench.config.yaml.YamlFiles
import io.github.junekim0007.cryptobench.config.yaml.YamlCodec
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File
import java.nio.file.Files

/** Every handler round-trips through a real file, and the shared file layer stamps and checks the version. */
class DocumentsTest {

    private val files = YamlFiles()
    private val codec = YamlCodec()
    private val directory: File = Files.createTempDirectory("documents").toFile()
    private val inventory = InventoryBuilder().build(
        CaptureSource.parse(codec.load(Fixtures.CAPTURE)), TrialSource.parse(codec.load(Fixtures.TRIAL)), InventoryBuilder.Files("probe_x.yaml", "trial_x.yaml"))
    private val global = GlobalDocument.parse(codec.load(Fixtures.GLOBAL))
    private val testSet = TestSetDocument.parse(codec.load(Fixtures.TEST_SET))
    private val effective = EffectiveBuilder().build(global, testSet, inventory, EffectiveBuilder.Files("global.yaml", "testsets/scope.yaml", "inventory.yaml"))

    /** One override feeds many entries the same list; the file must still read back as plain values. */
    @Test
    fun everyKindRoundTripsInFull() {
        val warned = effective.copy(warnings = listOf("override_matches_nothing: {name=X}"))
        assertEquals(inventory, files.at(File(directory, "inventory.yaml"), InventoryDocument).let { it.write(inventory); it.read() })
        assertEquals(warned, files.at(File(directory, "effective.yaml"), EffectiveDocument).let { it.write(warned); it.read() })
        assertEquals(global, files.at(File(directory, "global.yaml"), GlobalDocument).let { it.write(global); it.read() })
        assertEquals(testSet, files.at(File(directory, "scope.yaml"), TestSetDocument).let { it.write(testSet); it.read() })
        val text = File(directory, "effective.yaml").readText()
        assertTrue(text, !text.contains("&id") && !text.contains("*id"))
    }

    @Test
    fun theFileLayerStampsAndChecksTheVersion() {
        val written = files.at(File(directory, "inventory.yaml"), InventoryDocument).write(inventory)
        assertTrue(written.readText().startsWith("schemaVersion: 1\n"))
        written.writeText(written.readText().replaceFirst("schemaVersion: 1", "schemaVersion: 9"))
        assertEquals("unsupported_schema_version: inventory.yaml: 9, this build reads 1",
            assertThrows(IllegalArgumentException::class.java) { files.at(written, InventoryDocument).read() }.message)
    }

    /** A misspelt section, key or choice fails by name instead of quietly falling back to defaults. */
    @Test
    fun malformedDocumentsAreRefusedByName() {
        val global = "schemaVersion: 1\nselection: {testSet: a.yaml}\n"
        listOf<Pair<() -> Any, String>>(
            { GlobalDocument.parse(codec.load(global + "rn: {}\n")) } to "unknown_section: [rn], known [selection, run, policy, analysis]",
            { GlobalDocument.parse(codec.load(global + "run: {inputSize: [1]}\n")) } to "unknown_keys: run [inputSize], known [inputSizes, phases, metrics, processRepetitions, seed, harness]",
            { GlobalDocument.parse(codec.load(global + "policy: {onFailure: retry}\n")) } to "invalid: policy.onFailure retry, one of [stop, skip]",
            { GlobalDocument.parse(codec.load(global + "policy: {onUnavailable: skip}\n")) } to "unknown_keys: policy [onUnavailable], known [onFailure]",
            { GlobalDocument.parse(codec.load(global + "analysis: {statistic: {headline: average}}\n")) } to "invalid: analysis.statistic.headline average, one of [auto, median, mean]",
            { GlobalDocument.parse(codec.load(global + "analysis: {statistic: {meanUpToCovPercent: 0}}\n")) } to "not_positive: meanUpToCovPercent 0.0 at analysis.statistic",
            { GlobalDocument.parse(codec.load(global + "analysis: {statistic: {covLimit: 5}}\n")) } to "unknown_keys: analysis.statistic [covLimit], known [headline, meanUpToCovPercent]",
            { GlobalDocument.parse(codec.load(global + "analysis: {stat: {}}\n")) } to "unknown_keys: analysis [stat], known [statistic, charts, dir]",
            { GlobalDocument.parse(codec.load(global + "analysis: {charts: [bars]}\n")) } to "invalid: analysis.charts bars, one of [iqrBars, throughput, latency, stability]",
            { GlobalDocument.parse(codec.load(global + "analysis: {charts: [iqrBars, iqrbars]}\n")) } to "duplicate: charts [iqrBars, iqrBars] at analysis",
            { GlobalDocument.parse(codec.load(global + "analysis: {dir: ' '}\n")) } to "blank: dir at analysis",
            { GlobalDocument.parse(codec.load("schemaVersion: 1\nselection: {testSet: a.yaml, exclude: [{type: Mac}, {}]}\n")) } to "empty_rule: give provider, type or name at selection.exclude[1]",
            { TestSetDocument.parse(codec.load("schemaVersion: 1\noverrides:\n- {match: {type: Cipher}, set: {keySize: [1]}}\n")) } to "unknown_keys: overrides[0].set [keySize], known [keySizes, inputSizes, key, parameters, operations, harness]",
            { GlobalDocument.parse(codec.load(global + "run: {harness: {iterations: 0}}\n")) } to "not_positive: iterations 0 at run.harness",
            { GlobalDocument.parse(codec.load(global + "run: {harness: {profile: none}}\n")) } to "unknown_keys: run.harness [profile], known [iterations, warmupIterations, profiling]",
            { TestSetDocument.parse(codec.load("schemaVersion: 1\noverrides:\n- {match: {type: Cipher}, set: {harness: {profiling: flame}}}\n")) } to "invalid: profiling flame, known [none, MethodTracing, StackSampling] at overrides[0].set.harness",
            { codec.load("- one\n- two\n") } to "not_a_mapping: the document is not a set of key: value entries",
        ).forEach { (parse, expected) ->
            assertEquals(expected, assertThrows(IllegalArgumentException::class.java) { parse() }.message)
        }
        val duplicate = assertThrows(RuntimeException::class.java) { codec.load("schemaVersion: 1\nschemaVersion: 1\n") }.message!!
        assertTrue(duplicate, duplicate.contains("duplicate key"))
    }

    @Test
    fun aMissingRunSectionOrKeyKeepsDefaults() {
        val minimal = GlobalDocument.parse(codec.load("schemaVersion: 1\nselection: {testSet: testsets/all.yaml}\n"))
        assertEquals(listOf(1024), minimal.run.inputSizes)
        val partial = GlobalDocument.parse(codec.load("schemaVersion: 1\nselection: {testSet: testsets/all.yaml}\nrun: {processRepetitions: 3}\n"))
        assertEquals(3, partial.run.processRepetitions)
        assertEquals(listOf(1024), partial.run.inputSizes)
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
}
