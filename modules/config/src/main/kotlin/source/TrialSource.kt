package io.github.junekim0007.cryptobench.config.source

import io.github.junekim0007.cryptobench.config.write.DocumentFields.boolean
import io.github.junekim0007.cryptobench.config.write.DocumentFields.number
import io.github.junekim0007.cryptobench.config.write.DocumentFields.optionalBoolean
import io.github.junekim0007.cryptobench.config.write.DocumentFields.optionalNumber
import io.github.junekim0007.cryptobench.config.write.DocumentFields.optionalSection
import io.github.junekim0007.cryptobench.config.write.DocumentFields.optionalSections
import io.github.junekim0007.cryptobench.config.write.DocumentFields.optionalString
import io.github.junekim0007.cryptobench.config.write.DocumentFields.sections
import io.github.junekim0007.cryptobench.config.write.DocumentFields.string

/** Reads a trial document by its keys. Only names that were called with a default key become entries. */
object TrialSource {

    const val SUPPORTED_SCHEMA_VERSION = 2

    fun read(fileName: String, document: Map<String, Any>): TrialView {
        val schemaVersion = number(document, "schemaVersion").toInt()
        require(schemaVersion == SUPPORTED_SCHEMA_VERSION) {
            "unsupported_trial_schema: $schemaVersion, this build reads $SUPPORTED_SCHEMA_VERSION"
        }
        val entries = sections(document, "services").flatMap { service ->
            val provider = string(service, "provider")
            val type = string(service, "type")
            val own = optionalSection(service, "defaultRun")?.let { TrialView.Entry(provider, type, string(service, "algorithm"), defaultRun(it)) }
            val transformations = optionalSections(service, "transformations").mapNotNull { transformation ->
                optionalSection(transformation, "defaultRun")?.let { TrialView.Entry(provider, type, string(transformation, "name"), defaultRun(it)) }
            }
            listOfNotNull(own) + transformations
        }
        return TrialView(fileName, number(document, "capturedAtMillis").toLong(), entries)
    }

    private fun defaultRun(document: Map<String, Any>): TrialView.DefaultRun = TrialView.DefaultRun(
        works = boolean(document, "works"),
        keyAlgorithm = optionalString(document, "keyAlgorithm"),
        keyProvider = optionalString(document, "keyProvider"),
        keySize = optionalNumber(document, "keySize")?.toInt(),
        inputSize = optionalNumber(document, "inputSize")?.toInt(),
        providerChose = optionalString(document, "providerChose"),
        bareName = optionalBoolean(document, "bareName"),
        error = optionalString(document, "error"),
    )
}
