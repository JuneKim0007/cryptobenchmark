package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.config.effective.EffectiveBuilder
import io.github.junekim0007.cryptobench.config.effective.EffectiveDocument
import io.github.junekim0007.cryptobench.config.global.GlobalDocument
import io.github.junekim0007.cryptobench.config.global.dto.AnalysisSettings
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
