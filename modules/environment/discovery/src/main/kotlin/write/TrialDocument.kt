package io.github.junekim0007.cryptobench.discovery.write

import io.github.junekim0007.cryptobench.discovery.contract.ServiceTrialEntry
import io.github.junekim0007.cryptobench.discovery.contract.TransformationTrialEntry
import io.github.junekim0007.cryptobench.discovery.contract.TrialOutcome
import io.github.junekim0007.cryptobench.discovery.contract.TrialReport
import io.github.junekim0007.cryptobench.discovery.write.DocumentFields.boolean
import io.github.junekim0007.cryptobench.discovery.write.DocumentFields.number
import io.github.junekim0007.cryptobench.discovery.write.DocumentFields.optionalSections
import io.github.junekim0007.cryptobench.discovery.write.DocumentFields.optionalString
import io.github.junekim0007.cryptobench.discovery.write.DocumentFields.sections
import io.github.junekim0007.cryptobench.discovery.write.DocumentFields.string

object TrialDocument {

    const val SCHEMA_VERSION = "schemaVersion"
    const val CAPTURED_AT_MILLIS = "capturedAtMillis"
    const val SERVICES = "services"

    const val PROVIDER = "provider"
    const val TYPE = "type"
    const val ALGORITHM = "algorithm"
    const val INSTANTIATES = "instantiates"
    const val ERROR = "error"
    const val TRANSFORMATIONS = "transformations"
    const val NAME = "name"

    fun of(report: TrialReport): Map<String, Any> = linkedMapOf(
        SCHEMA_VERSION to report.schemaVersion,
        CAPTURED_AT_MILLIS to report.capturedAtMillis,
        SERVICES to report.services.map { serviceDocument(it) },
    )

    fun parse(document: Map<String, Any>): TrialReport {
        val schemaVersion = number(document, SCHEMA_VERSION).toInt()
        require(schemaVersion == TrialReport.SCHEMA_VERSION) {
            "unsupported_schema_version: $schemaVersion, this build reads ${TrialReport.SCHEMA_VERSION}"
        }
        return TrialReport(
            capturedAtMillis = number(document, CAPTURED_AT_MILLIS).toLong(),
            services = sections(document, SERVICES).map { serviceEntry(it) },
            schemaVersion = schemaVersion,
        )
    }

    private fun serviceDocument(service: ServiceTrialEntry): Map<String, Any> {
        val document = linkedMapOf<String, Any>(
            PROVIDER to service.provider,
            TYPE to service.type,
            ALGORITHM to service.algorithm,
        )
        outcome(document, service.outcome)
        if (service.transformations.isNotEmpty()) {
            document[TRANSFORMATIONS] = service.transformations.map { transformationDocument(it) }
        }
        return document
    }

    private fun serviceEntry(document: Map<String, Any>): ServiceTrialEntry = ServiceTrialEntry(
        provider = string(document, PROVIDER),
        type = string(document, TYPE),
        algorithm = string(document, ALGORITHM),
        outcome = outcome(document),
        transformations = optionalSections(document, TRANSFORMATIONS).map { transformationEntry(it) },
    )

    private fun transformationDocument(transformation: TransformationTrialEntry): Map<String, Any> {
        val document = linkedMapOf<String, Any>(NAME to transformation.name)
        outcome(document, transformation.outcome)
        return document
    }

    private fun transformationEntry(document: Map<String, Any>): TransformationTrialEntry =
        TransformationTrialEntry(name = string(document, NAME), outcome = outcome(document))

    private fun outcome(document: MutableMap<String, Any>, outcome: TrialOutcome) {
        document[INSTANTIATES] = outcome.instantiates
        if (!outcome.instantiates) {
            document[ERROR] = outcome.error
        }
    }

    private fun outcome(document: Map<String, Any>): TrialOutcome =
        TrialOutcome(instantiates = boolean(document, INSTANTIATES), error = optionalString(document, ERROR))
}
