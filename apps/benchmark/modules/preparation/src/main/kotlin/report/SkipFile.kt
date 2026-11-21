package io.github.junekim0007.cryptobench.preparation.report

import io.github.junekim0007.cryptobench.records.Skip
import io.github.junekim0007.cryptobench.document.DocumentFields
import io.github.junekim0007.cryptobench.files.FileNames
import io.github.junekim0007.cryptobench.document.versioned.DocumentHandler
import io.github.junekim0007.cryptobench.document.versioned.YamlFiles
import java.io.File

class SkipFile(private val directory: File) {

    val file: File get() = File(directory, FileNames.SKIPPED)

    private val versioned get() = YamlFiles().at(file, Document)

    fun write(skipped: List<Skip>): File = versioned.write(skipped)

    // A process per case adds its own skip to what the listing wrote.
    fun added(skip: Skip): File = write(read() + skip)

    fun read(): List<Skip> = versioned.read()

    private object Document : DocumentHandler<List<Skip>> {
        private const val SKIPPED = "skipped"
        private const val SCHEMA_VERSION = 2

        override val schemaVersion = SCHEMA_VERSION

        override fun parse(document: Map<String, Any>): List<Skip> = DocumentFields.sections(document, SKIPPED).map(Skip::read)

        override fun of(value: List<Skip>): Map<String, Any> = linkedMapOf(SKIPPED to value.map(Skip::fields))
    }
}
