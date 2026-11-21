package io.github.junekim0007.cryptobench.config.source

import io.github.junekim0007.cryptobench.document.versioned.DocumentReader
import io.github.junekim0007.cryptobench.document.DocumentFields.number
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalSections
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalStrings
import io.github.junekim0007.cryptobench.document.DocumentFields.section
import io.github.junekim0007.cryptobench.document.DocumentFields.sections
import io.github.junekim0007.cryptobench.document.DocumentFields.string

object CaptureSource : DocumentReader<CaptureView> {

    override val schemaVersion: Int = 1

    override fun parse(document: Map<String, Any>): CaptureView {
        val providers = sections(document, "providers").sortedBy { number(it, "precedence").toInt() }
        return CaptureView(
            capturedAtMillis = number(document, "capturedAtMillis").toLong(),
            device = LinkedHashMap(section(document, "runtime")),
            providers = providers.map { string(it, "name") },
            aliases = providers.associate { provider ->
                string(provider, "name") to optionalSections(provider, "services")
                    .map { CaptureView.service(string(it, "type"), string(it, "algorithm")) to optionalStrings(it, "aliases") }
                    .filter { it.second.isNotEmpty() }.toMap()
            },
        )
    }
}
