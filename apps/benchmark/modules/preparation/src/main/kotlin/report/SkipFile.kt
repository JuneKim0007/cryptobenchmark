package io.github.junekim0007.cryptobench.preparation.report

import io.github.junekim0007.cryptobench.files.FileNames
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFile
import java.io.File

class SkipFile(private val directory: File) {

    val file: File get() = File(directory, FileNames.SKIPPED)

    fun write(skipped: List<Skip>): File {
        val document = linkedMapOf<String, Any>(
            "schemaVersion" to SCHEMA_VERSION,
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

    // A process per case adds its own skip to what the listing wrote.
    fun added(skip: Skip): File = write(read() + skip)

    fun read(): List<Skip> =
        DocumentFields.sections(DocumentFile.read(file, "skipped", SCHEMA_VERSION), "skipped").map { entry ->
            Skip(entry["stage"].toString(), entry["provider"]?.toString(), entry["type"]?.toString(), entry["name"]?.toString(), entry["reason"].toString())
        }

    companion object {
        private const val SCHEMA_VERSION = 1
    }
}
