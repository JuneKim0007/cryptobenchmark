package io.github.junekim0007.cryptobench.preparation.inbound

import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields.expectKeys
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields.section
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFile
import java.io.File

object InboundFile {

    const val SUPPORTED_SCHEMA_VERSION = 1

    private const val SCHEMA_NAME = "config"

    // Every key :config writes; preparation reads run, policy, providers and runId.
    private val KEYS = listOf("schemaVersion", "generatedFrom", "runId", "run", "policy", "analysis", "bundledProviders", "providers", "warnings", "skipped")

    fun read(file: File): InboundDocument =
        inbound(file.name, DocumentFile.read(file, SCHEMA_NAME, SUPPORTED_SCHEMA_VERSION))

    fun read(fileName: String, text: String): InboundDocument =
        inbound(fileName, DocumentFile.read(fileName, text, SCHEMA_NAME, SUPPORTED_SCHEMA_VERSION))

    private fun inbound(fileName: String, document: Map<String, Any>): InboundDocument {
        expectKeys(document, KEYS, fileName)
        return InboundDocument(fileName, (document["runId"] as? String)?.takeIf { it.isNotBlank() }, section(document, "run"), section(document, "policy"), section(document, "providers"))
    }
}
