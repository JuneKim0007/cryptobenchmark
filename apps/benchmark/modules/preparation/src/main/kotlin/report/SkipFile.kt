package io.github.junekim0007.cryptobench.preparation.report

import io.github.junekim0007.cryptobench.records.Skip
import io.github.junekim0007.cryptobench.document.DocumentFields
import io.github.junekim0007.cryptobench.files.FileNames
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFile
import java.io.File

class SkipFile(private val directory: File) {

    val file: File get() = File(directory, FileNames.SKIPPED)

    fun write(skipped: List<Skip>): File {
        val document = linkedMapOf<String, Any>(
            "schemaVersion" to SCHEMA_VERSION,
            "skipped" to skipped.map(Skip::fields),
        )
        return DocumentFile.write(file, document)
    }

    // A process per case adds its own skip to what the listing wrote.
    fun added(skip: Skip): File = write(read() + skip)

    fun read(): List<Skip> =
        DocumentFields.sections(DocumentFile.read(file, SCHEMA_VERSION), "skipped").map(Skip::read)

    companion object {
        private const val SCHEMA_VERSION = 2
    }
}
