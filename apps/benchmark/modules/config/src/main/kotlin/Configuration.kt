package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.config.effective.EffectiveBuilder
import io.github.junekim0007.cryptobench.config.effective.EffectiveDocument
import io.github.junekim0007.cryptobench.config.effective.ReportDocument
import io.github.junekim0007.cryptobench.config.effective.dto.EffectiveConfig
import io.github.junekim0007.cryptobench.config.effective.dto.Report
import io.github.junekim0007.cryptobench.config.inventory.InventoryBuilder
import io.github.junekim0007.cryptobench.config.inventory.InventoryDocument
import io.github.junekim0007.cryptobench.config.source.CaptureSource
import io.github.junekim0007.cryptobench.config.source.TrialSource
import io.github.junekim0007.cryptobench.config.yaml.YamlCodec
import io.github.junekim0007.cryptobench.config.yaml.YamlFiles
import io.github.junekim0007.cryptobench.settings.Facts
import java.io.File
import java.nio.file.Files

class Configuration(
    private val output: File,
    private val files: YamlFiles = YamlFiles(),
    private val inventoryBuilder: InventoryBuilder = InventoryBuilder(),
    private val effectiveBuilder: EffectiveBuilder = EffectiveBuilder(),
) {

    val inventoryFile: File get() = File(output, INVENTORY)

    val effectiveFile: File get() = File(output, EFFECTIVE)

    val reportFile: File get() = File(output, REPORT)

    fun inventory(captureFile: File, trialFile: File): File {
        Files.deleteIfExists(inventoryFile.toPath())
        val capture = files.readOnly(captureFile, CaptureSource).read()
        val trial = files.readOnly(trialFile, TrialSource).read()
        val inventory = inventoryBuilder.build(capture, trial, InventoryBuilder.Files(captureFile.name, trialFile.name))
        return files.at(inventoryFile, InventoryDocument).write(inventory)
    }

    fun effective(globalFile: File, inventoryFile: File = this.inventoryFile, factsFile: File? = null): File {
        Files.deleteIfExists(effectiveFile.toPath())
        Files.deleteIfExists(reportFile.toPath())
        val (global, testSet) = AuthoredFiles(files).read(globalFile)
        val inventory = files.at(inventoryFile, InventoryDocument).read()
        val facts = factsFile?.let(::readFacts) ?: Facts.UNKNOWN
        val effective = effectiveBuilder.build(global, testSet, inventory, EffectiveBuilder.Files(globalFile.name, global.selection.testSet, inventoryFile.name), facts)
        files.at(reportFile, ReportDocument).write(Report(effective.runId, effective.warnings, effective.skipped))
        return files.at(effectiveFile, EffectiveDocument).write(effective)
    }

    /** The settings, with what the run noticed joined back from the report file beside them when there is one. */
    fun readEffective(file: File = effectiveFile): EffectiveConfig {
        val effective = files.at(file, EffectiveDocument).read()
        val report = File(file.absoluteFile.parentFile, REPORT).takeIf { it.isFile } ?: return effective
        val noticed = files.at(report, ReportDocument).read()
        return effective.copy(warnings = effective.warnings + noticed.warnings, skipped = effective.skipped + noticed.skipped)
    }

    private fun readFacts(file: File): Facts {
        require(file.isFile) { "missing_file: ${file.path} (--facts)" }
        return try {
            Facts.read(YamlCodec().load(file.readText()))
        } catch (malformed: RuntimeException) {
            if (malformed is IllegalArgumentException) throw malformed
            throw IllegalArgumentException("unreadable_yaml: ${file.path}: ${malformed.message}", malformed)
        }
    }

    companion object {
        const val INVENTORY = "inventory.yaml"
        const val EFFECTIVE = "effective.yaml"
        const val REPORT = "report.yaml"
    }
}
