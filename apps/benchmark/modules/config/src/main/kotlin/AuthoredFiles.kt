package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.config.global.GlobalDocument
import io.github.junekim0007.cryptobench.config.global.dto.GlobalConfig
import io.github.junekim0007.cryptobench.config.testset.TestSetDocument
import io.github.junekim0007.cryptobench.config.testset.dto.TestSet
import io.github.junekim0007.cryptobench.config.yaml.YamlFiles
import io.github.junekim0007.cryptobench.files.Beside
import java.io.File

data class Authored(val global: GlobalConfig, val testSet: TestSet, val testSetFile: File)

/** A global.yaml and its test set through their parsers; no capture, no inventory, nothing written. */
class AuthoredFiles(private val files: YamlFiles = YamlFiles()) {

    fun read(globalFile: File): Authored {
        require(globalFile.isFile) { "missing_file: ${globalFile.path}" }
        val global = files.at(globalFile, GlobalDocument).read()
        val testSetFile = Beside.authored(globalFile, global.selection.testSet)
        require(testSetFile.isFile) { "missing_file: ${testSetFile.path} (${globalFile.name} selection.testSet: ${global.selection.testSet})" }
        return Authored(global, files.at(testSetFile, TestSetDocument).read(), testSetFile)
    }
}
