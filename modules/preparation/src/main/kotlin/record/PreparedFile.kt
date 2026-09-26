package io.github.junekim0007.cryptobench.preparation.record

import io.github.junekim0007.cryptobench.preparation.global.HarnessSettings
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedRun
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFile
import java.io.File

class PreparedFile(private val directory: File) {

    val file: File get() = File(directory, NAME)

    internal fun write(run: PreparedRun, effectiveFileName: String, harness: HarnessSettings, seed: Long): File =
        DocumentFile.write(file, PreparedDocument.of(run, effectiveFileName, harness, seed))

    companion object {
        const val NAME = "prepared.yaml"
    }
}
