package io.github.junekim0007.cryptobench.config.source

import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.boolean
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.number
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalBoolean
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalNumber
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalSection
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalSections
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalString
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.sections
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.string
import io.github.junekim0007.cryptobench.config.yaml.DocumentReader

/** Reads a trial document by its keys. Only names that were called with a default key become entries. */
object TrialSource : DocumentReader<TrialView> {

    override val schemaVersion: Int = 2

    override fun parse(document: Map<String, Any>): TrialView {
        val entries = sections(document, "services").flatMap { service ->
            val provider = string(service, "provider")
            val type = string(service, "type")
            val own = optionalSection(service, "defaultRun")?.let { TrialView.Entry(provider, type, string(service, "algorithm"), defaultRun(it)) }
            val transformations = optionalSections(service, "transformations").mapNotNull { transformation ->
                optionalSection(transformation, "defaultRun")?.let { TrialView.Entry(provider, type, string(transformation, "name"), defaultRun(it)) }
            }
            listOfNotNull(own) + transformations
        }
        return TrialView(number(document, "capturedAtMillis").toLong(), entries)
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
