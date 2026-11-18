package io.github.junekim0007.cryptobench.config.global

import io.github.junekim0007.cryptobench.config.global.dto.AnalysisSettings

/** parity/defaults.yaml: the value :config writes for each key a config leaves out, which Python reads instead of a copy. */
object DefaultsDocument {

    const val SCHEMA_VERSION = 1
    const val HEADER = "# written by :config DefaultsDocument (-Dexamples.update); read by lib/cryptobench/cryptobench/shared/settings/defaults.py\n"

    fun of(): Map<String, Any> = linkedMapOf(
        "schemaVersion" to SCHEMA_VERSION,
        "run" to RunDocument.defaults(),
        "analysis" to AnalysisDocument.of(AnalysisSettings()),
    )
}
