package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.config.effective.EffectiveBuilder
import io.github.junekim0007.cryptobench.config.effective.EffectiveDocument
import io.github.junekim0007.cryptobench.config.effective.dto.EffectiveConfig
import io.github.junekim0007.cryptobench.config.global.GlobalDocument
import io.github.junekim0007.cryptobench.config.inventory.InventoryBuilder
import io.github.junekim0007.cryptobench.config.inventory.InventoryDocument
import io.github.junekim0007.cryptobench.config.source.CaptureSource
import io.github.junekim0007.cryptobench.config.source.TrialSource
import io.github.junekim0007.cryptobench.config.testset.TestSetDocument
import io.github.junekim0007.cryptobench.config.yaml.YamlFiles
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

    fun inventory(captureFile: File, trialFile: File): File {
        Files.deleteIfExists(inventoryFile.toPath())
        val capture = files.readOnly(captureFile, CaptureSource).read()
        val trial = files.readOnly(trialFile, TrialSource).read()
        val inventory = inventoryBuilder.build(capture, trial, InventoryBuilder.Files(captureFile.name, trialFile.name))
        return files.at(inventoryFile, InventoryDocument).write(inventory)
    }

    fun effective(globalFile: File, inventoryFile: File = this.inventoryFile): File {
        Files.deleteIfExists(effectiveFile.toPath())
        val global = files.at(globalFile, GlobalDocument).read()
        val named = File(global.selection.testSet)
        val testSetFile = if (named.isAbsolute) named else File(globalFile.absoluteFile.parentFile, global.selection.testSet)
        require(testSetFile.isFile) { "missing_file: ${testSetFile.path} (${globalFile.name} selection.testSet: ${global.selection.testSet})" }
        val testSet = files.at(testSetFile, TestSetDocument).read()
        val inventory = files.at(inventoryFile, InventoryDocument).read()
        val effective = effectiveBuilder.build(global, testSet, inventory, EffectiveBuilder.Files(globalFile.name, global.selection.testSet, inventoryFile.name))
        return files.at(effectiveFile, EffectiveDocument).write(effective)
    }

    fun readEffective(file: File = effectiveFile): EffectiveConfig = files.at(file, EffectiveDocument).read()

    companion object {
        const val INVENTORY = "inventory.yaml"
        const val EFFECTIVE = "effective.yaml"
    }
}
