package io.github.junekim0007.cryptobench.preparation.inbound

import io.github.junekim0007.cryptobench.document.SchemaVersion
import io.github.junekim0007.cryptobench.document.DocumentFields.expectKeys
import io.github.junekim0007.cryptobench.document.DocumentFields.section
import io.github.junekim0007.cryptobench.document.versioned.DocumentReader
import io.github.junekim0007.cryptobench.document.versioned.YamlFiles
import java.io.File

object InboundFile {

    const val SUPPORTED_SCHEMA_VERSION = 2

    private const val ROOT = "effective"

    // Every key :config writes; preparation reads run, policy, providers and runId.
    private val KEYS = listOf(SchemaVersion.FIELD, "generatedFrom", "runId", "run", "policy", "analysis", "bundledProviders", "providers", "warnings", "skipped")

    fun read(file: File): InboundDocument = YamlFiles().readOnly(file, Reader(file.name)).read()

    fun read(fileName: String, text: String): InboundDocument = YamlFiles().readOnly(File(fileName), Reader(fileName)).read(text)

    // the file name is the document's own field, never part of a refusal: VersionedFile adds that
    private class Reader(private val fileName: String) : DocumentReader<InboundDocument> {

        override val schemaVersion = SUPPORTED_SCHEMA_VERSION

        override fun parse(document: Map<String, Any>): InboundDocument {
            expectKeys(document, KEYS, ROOT)
            return InboundDocument(fileName, (document["runId"] as? String)?.takeIf { it.isNotBlank() }, section(document, "run"), section(document, "policy"), section(document, "providers"))
        }
    }
}
