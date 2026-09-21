package io.github.junekim0007.cryptobench.config.source

import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.number
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.section
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.sections
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.string
import io.github.junekim0007.cryptobench.config.yaml.DocumentReader

/** Reads environment's probe document by its keys; the configuration does not depend on the environment module's classes. */
object CaptureSource : DocumentReader<CaptureView> {

    override val schemaVersion: Int = 1

    override fun parse(document: Map<String, Any>): CaptureView {
        return CaptureView(
            capturedAtMillis = number(document, "capturedAtMillis").toLong(),
            device = LinkedHashMap(section(document, "runtime")),
            providers = sections(document, "providers")
                .sortedBy { number(it, "precedence").toInt() }
                .map { string(it, "name") },
        )
    }
}
