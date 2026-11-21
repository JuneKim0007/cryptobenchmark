package io.github.junekim0007.cryptobench.preparation.record

import io.github.junekim0007.cryptobench.document.DocumentFields
import io.github.junekim0007.cryptobench.files.FileNames
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.prepare.Listing
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import io.github.junekim0007.cryptobench.document.versioned.DocumentHandler
import io.github.junekim0007.cryptobench.document.versioned.YamlFiles
import java.io.File

/** prepared.yaml: written once from the listing, then each case's entry replaced when it is prepared or removed when it is not; a process per case edits only its own. */
class PreparedFile(private val directory: File) {

    val file: File get() = File(directory, FileNames.PREPARED)

    private val versioned get() = YamlFiles().at(file, Document)

    fun listed(listing: Listing, cases: List<BenchmarkCase>): File = versioned.write(PreparedDocument.of(listing, cases))

    fun prepared(prepared: PreparedCase): File = edited(prepared.case.id) { PreparedDocument.case(prepared) }

    fun failed(id: String): File = edited(id) { null }

    private fun edited(id: String, entry: () -> Map<String, Any>?): File {
        val document = LinkedHashMap(versioned.read())
        document[CASES] = DocumentFields.sections(document, CASES).mapNotNull { case -> if (case["id"] == id) entry() else case }
        return versioned.write(document)
    }

    // read whole and written back whole; parse refuses a file without its cases
    private object Document : DocumentHandler<Map<String, Any>> {

        override val schemaVersion = PreparedDocument.SCHEMA_VERSION

        override fun parse(document: Map<String, Any>): Map<String, Any> = document.also { DocumentFields.sections(it, CASES) }

        override fun of(value: Map<String, Any>): Map<String, Any> = value
    }

    private companion object {
        const val CASES = "cases"
    }
}
