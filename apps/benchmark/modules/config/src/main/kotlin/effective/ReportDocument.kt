package io.github.junekim0007.cryptobench.config.effective

import io.github.junekim0007.cryptobench.config.effective.dto.Report
import io.github.junekim0007.cryptobench.config.yaml.DocumentHandler
import io.github.junekim0007.cryptobench.config.yaml.ReadOnlyYamlFile
import io.github.junekim0007.cryptobench.document.DocumentFields.expectKeys
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalSections
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalStringOrNull
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalStrings
import io.github.junekim0007.cryptobench.settings.Skip

object ReportDocument : DocumentHandler<Report> {

    override val schemaVersion: Int = 2

    private const val RUN_ID = "runId"
    private const val WARNINGS = "warnings"
    private const val SKIPPED = "skipped"

    override fun of(value: Report): Map<String, Any> = LinkedHashMap<String, Any>().apply {
        value.runId?.let { put(RUN_ID, it) }
        put(WARNINGS, value.warnings)
        put(SKIPPED, value.skipped.map(Skip::fields))
    }

    override fun parse(document: Map<String, Any>): Report {
        expectKeys(document, listOf(ReadOnlyYamlFile.SCHEMA_VERSION, RUN_ID, WARNINGS, SKIPPED), "report")
        return Report(
            runId = optionalStringOrNull(document, RUN_ID),
            warnings = optionalStrings(document, WARNINGS),
            skipped = optionalSections(document, SKIPPED).map(Skip::read),
        )
    }
}
