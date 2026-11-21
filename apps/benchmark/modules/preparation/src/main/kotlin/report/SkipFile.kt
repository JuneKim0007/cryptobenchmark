package io.github.junekim0007.cryptobench.preparation.report

import io.github.junekim0007.cryptobench.records.Skip
import io.github.junekim0007.cryptobench.document.DocumentFields
import io.github.junekim0007.cryptobench.files.FileNames
import io.github.junekim0007.cryptobench.document.versioned.MapDocument
import io.github.junekim0007.cryptobench.document.versioned.YamlFiles
import java.io.File

class SkipFile(private val directory: File) {

    val file: File get() = File(directory, FileNames.SKIPPED)

    private val versioned get() = YamlFiles().at(file, MapDocument(SCHEMA_VERSION))

    fun write(skipped: List<Skip>): File {
        val document = linkedMapOf<String, Any>(
            "schemaVersion" to SCHEMA_VERSION,
            "skipped" to skipped.map(Skip::fields),
        )
        return versioned.write(document)
    }

    // A process per case adds its own skip to what the listing wrote.
    fun added(skip: Skip): File = write(read() + skip)

    fun read(): List<Skip> =
        DocumentFields.sections(versioned.read(), "skipped").map(Skip::read)

    companion object {
        private const val SCHEMA_VERSION = 2
    }
}
