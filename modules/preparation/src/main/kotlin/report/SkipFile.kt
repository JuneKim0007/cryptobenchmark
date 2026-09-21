package io.github.junekim0007.cryptobench.preparation.report

import io.github.junekim0007.cryptobench.preparation.shared.YamlCodec
import java.io.File
import java.io.IOException

class SkipFile(private val directory: File) {

    val file: File get() = File(directory, NAME)

    fun write(skipped: List<Skip>): File {
        if (!directory.exists() && !directory.mkdirs()) {
            throw IOException("cannot create ${directory.absolutePath}")
        }
        val document = linkedMapOf<String, Any>(
            "schemaVersion" to 1,
            "skipped" to skipped.map { skip ->
                LinkedHashMap<String, Any>().apply {
                    put("stage", skip.stage)
                    skip.provider?.let { put("provider", it) }
                    skip.type?.let { put("type", it) }
                    skip.name?.let { put("name", it) }
                    put("reason", skip.reason)
                }
            },
        )
        file.writeText(YamlCodec().dump(document), Charsets.UTF_8)
        return file
    }

    companion object {
        const val NAME = "skipped.yaml"
    }
}
