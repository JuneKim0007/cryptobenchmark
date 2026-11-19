package io.github.junekim0007.cryptobench.preparation.inbound

import io.github.junekim0007.cryptobench.document.DocumentFields.expectKeys
import io.github.junekim0007.cryptobench.document.DocumentFields.section
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFile
import java.io.File

object InboundFile {

    const val SUPPORTED_SCHEMA_VERSION = 2


    // Every key :config writes; preparation reads run, policy, providers and runId.
    private val KEYS = listOf("schemaVersion", "generatedFrom", "runId", "run", "policy", "analysis", "bundledProviders", "providers", "warnings", "skipped")

    fun read(file: File): InboundDocument =
        inbound(file.name, DocumentFile.read(file, SUPPORTED_SCHEMA_VERSION))

    fun read(fileName: String, text: String): InboundDocument =
        inbound(fileName, DocumentFile.read(fileName, text, SUPPORTED_SCHEMA_VERSION))

    private fun inbound(fileName: String, document: Map<String, Any>): InboundDocument {
        expectKeys(document, KEYS, fileName)
        return InboundDocument(fileName, (document["runId"] as? String)?.takeIf { it.isNotBlank() }, section(document, "run"), section(document, "policy"), section(document, "providers"))
    }
}
