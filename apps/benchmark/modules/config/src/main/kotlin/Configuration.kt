package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.contract.Handoff
import io.github.junekim0007.cryptobench.config.effective.EffectiveBuilder
import io.github.junekim0007.cryptobench.config.effective.EffectiveDocument
import io.github.junekim0007.cryptobench.config.effective.ReportDocument
import io.github.junekim0007.cryptobench.config.effective.dto.EffectiveConfig
import io.github.junekim0007.cryptobench.config.effective.dto.Report
import io.github.junekim0007.cryptobench.config.inventory.InventoryBuilder
import io.github.junekim0007.cryptobench.config.inventory.InventoryDocument
import io.github.junekim0007.cryptobench.config.global.RunDocument
import io.github.junekim0007.cryptobench.config.layers.Provenance
import io.github.junekim0007.cryptobench.config.source.CaptureView
import io.github.junekim0007.cryptobench.config.source.FactsSource
import io.github.junekim0007.cryptobench.config.source.TrialView
import io.github.junekim0007.cryptobench.document.versioned.YamlFiles
import io.github.junekim0007.cryptobench.files.Beside
import io.github.junekim0007.cryptobench.files.FileNames
import io.github.junekim0007.cryptobench.settings.Facts
import java.io.File
import java.nio.file.Files

class Configuration(
    private val output: File,
    private val files: YamlFiles = YamlFiles(),
    private val inventoryBuilder: InventoryBuilder = InventoryBuilder(),
    private val effectiveBuilder: EffectiveBuilder = EffectiveBuilder(),
) {

    val inventoryFile: File get() = File(output, FileNames.INVENTORY)

    val effectiveFile: File get() = File(output, FileNames.EFFECTIVE)

    val reportFile: File get() = File(output, FileNames.CONFIG_REPORT)

    fun inventory(captureFile: File, trialFile: File): File {
        Files.deleteIfExists(inventoryFile.toPath())
        val handoff = Handoff.read(captureFile, trialFile)
        val inventory = inventoryBuilder.build(CaptureView.of(handoff.capture), TrialView.of(handoff.trial), InventoryBuilder.Files(captureFile.name, trialFile.name))
        return files.at(inventoryFile, InventoryDocument).write(inventory)
    }

    /** notes: what the runtime left out before configuring, such as a host's skipped bundled providers; written first among the warnings. */
    fun effective(globalFile: File, inventoryFile: File = this.inventoryFile, factsFile: File? = null, notes: List<String>): File {
        Files.deleteIfExists(effectiveFile.toPath())
        Files.deleteIfExists(reportFile.toPath())
        val (global, testSet, _, stack) = AuthoredFiles(files).read(globalFile)
        val inventory = files.at(inventoryFile, InventoryDocument).read()
        val facts = factsFile?.let(::readFacts) ?: Facts.UNKNOWN
        val built = effectiveBuilder.build(global, testSet, inventory, EffectiveBuilder.Files(globalFile.name, global.selection.testSet, inventoryFile.name), facts)
        val effective = built.copy(warnings = notes + built.warnings, generatedFrom = built.generatedFrom.copy(layers = stack.layers,
            settings = Provenance.settings(EffectiveDocument.settingsOf(built), stack, RunDocument.inherited(built.run, "run"))))
        files.at(reportFile, ReportDocument).write(Report(effective.runId, effective.warnings, effective.skipped))
        return files.at(effectiveFile, EffectiveDocument).write(effective)
    }

    /** The settings, with what the run noticed joined back from the report file beside them when there is one. */
    fun readEffective(file: File = effectiveFile): EffectiveConfig {
        val effective = files.at(file, EffectiveDocument).read()
        val report = Beside.file(file, FileNames.CONFIG_REPORT).takeIf { it.isFile } ?: return effective
        val noticed = files.at(report, ReportDocument).read()
        return effective.copy(warnings = effective.warnings + noticed.warnings, skipped = effective.skipped + noticed.skipped)
    }

    private fun readFacts(file: File): Facts = files.readOnly(file, FactsSource).read()
}
