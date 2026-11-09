package io.github.junekim0007.cryptobench.preparation.record

import io.github.junekim0007.cryptobench.files.FileNames
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.prepare.Listing
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFile
import java.io.File

/** prepared.yaml: written once from the listing, then each case's entry replaced when it is prepared or removed when it is not; a process per case edits only its own. */
class PreparedFile(private val directory: File) {

    val file: File get() = File(directory, FileNames.PREPARED)

    fun listed(listing: Listing, cases: List<BenchmarkCase>): File = DocumentFile.write(file, PreparedDocument.of(listing, cases))

    fun prepared(prepared: PreparedCase): File = edited(prepared.case.id) { PreparedDocument.case(prepared) }

    fun failed(id: String): File = edited(id) { null }

    private fun edited(id: String, entry: () -> Map<String, Any>?): File {
        val document = LinkedHashMap(DocumentFile.read(file, "prepared", PreparedDocument.SCHEMA_VERSION))
        document["cases"] = DocumentFields.sections(document, "cases").mapNotNull { case -> if (case["id"] == id) entry() else case }
        return DocumentFile.write(file, document)
    }
}
