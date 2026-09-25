package io.github.junekim0007.cryptobench.preparation.record

import io.github.junekim0007.cryptobench.preparation.global.HarnessSettings
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedRun
import io.github.junekim0007.cryptobench.preparation.shared.YamlCodec
import java.io.File
import java.io.IOException

class PreparedFile(private val directory: File) {

    val file: File get() = File(directory, NAME)

    internal fun write(run: PreparedRun, effectiveFileName: String, harness: HarnessSettings, seed: Long): File {
        if (!directory.exists() && !directory.mkdirs()) {
            throw IOException("cannot create ${directory.absolutePath}")
        }
        file.writeText(YamlCodec().dump(PreparedDocument.of(run, effectiveFileName, harness, seed)), Charsets.UTF_8)
        return file
    }

    companion object {
        const val NAME = "prepared.yaml"
    }
}
