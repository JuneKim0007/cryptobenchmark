package io.github.junekim0007.cryptobench.preparation.inbound

import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields.section
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFile
import java.io.File

object InboundFile {

    const val SUPPORTED_SCHEMA_VERSION = 1

    private const val SCHEMA_NAME = "config"

    fun read(file: File): InboundDocument =
        inbound(file.name, DocumentFile.read(file, SCHEMA_NAME, SUPPORTED_SCHEMA_VERSION))

    fun read(fileName: String, text: String): InboundDocument =
        inbound(fileName, DocumentFile.read(fileName, text, SCHEMA_NAME, SUPPORTED_SCHEMA_VERSION))

    private fun inbound(fileName: String, document: Map<String, Any>): InboundDocument =
        InboundDocument(fileName, (document["runId"] as? String)?.takeIf { it.isNotBlank() }, section(document, "run"), section(document, "policy"), section(document, "providers"))
}
