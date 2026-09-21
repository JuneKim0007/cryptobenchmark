package io.github.junekim0007.cryptobench.config.source

import io.github.junekim0007.cryptobench.config.write.DocumentFields.number
import io.github.junekim0007.cryptobench.config.write.DocumentFields.section
import io.github.junekim0007.cryptobench.config.write.DocumentFields.sections
import io.github.junekim0007.cryptobench.config.write.DocumentFields.string

/** Reads a probe document by its keys; the configuration does not depend on the environment module's classes. */
object CaptureSource {

    const val SUPPORTED_SCHEMA_VERSION = 1

    fun read(fileName: String, document: Map<String, Any>): CaptureView {
        val schemaVersion = number(document, "schemaVersion").toInt()
        require(schemaVersion == SUPPORTED_SCHEMA_VERSION) {
            "unsupported_capture_schema: $schemaVersion, this build reads $SUPPORTED_SCHEMA_VERSION"
        }
        return CaptureView(
            fileName = fileName,
            capturedAtMillis = number(document, "capturedAtMillis").toLong(),
            device = LinkedHashMap(section(document, "runtime")),
            providers = sections(document, "providers")
                .sortedBy { number(it, "precedence").toInt() }
                .map { string(it, "name") },
        )
    }
}
