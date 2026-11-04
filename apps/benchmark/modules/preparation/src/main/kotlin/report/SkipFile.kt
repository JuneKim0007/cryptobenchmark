package io.github.junekim0007.cryptobench.preparation.report

import io.github.junekim0007.cryptobench.preparation.shared.DocumentFile
import java.io.File

class SkipFile(private val directory: File) {

    val file: File get() = File(directory, NAME)

    fun write(skipped: List<Skip>): File {
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
        return DocumentFile.write(file, document)
    }

    companion object {
        const val NAME = "skipped.yaml"
    }
}
