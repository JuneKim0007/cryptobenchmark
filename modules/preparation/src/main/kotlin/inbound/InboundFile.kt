package io.github.junekim0007.cryptobench.preparation.inbound

import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields.number
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields.section
import io.github.junekim0007.cryptobench.preparation.shared.YamlCodec
import java.io.File

object InboundFile {

    const val SUPPORTED_SCHEMA_VERSION = 1

    fun read(file: File): InboundDocument = read(file.name, file.readText())

    fun read(fileName: String, text: String): InboundDocument {
        val document = YamlCodec().load(text)
        val schemaVersion = number(document, "schemaVersion").toInt()
        require(schemaVersion == SUPPORTED_SCHEMA_VERSION) {
            "unsupported_config_schema: $fileName: $schemaVersion, this build reads $SUPPORTED_SCHEMA_VERSION"
        }
        return InboundDocument(fileName, section(document, "run"), section(document, "policy"), section(document, "providers"))
    }
}
