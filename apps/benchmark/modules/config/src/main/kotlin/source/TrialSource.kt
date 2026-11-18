package io.github.junekim0007.cryptobench.config.source

import io.github.junekim0007.cryptobench.config.inventory.dto.KeystoreRow
import io.github.junekim0007.cryptobench.config.yaml.DocumentReader
import io.github.junekim0007.cryptobench.document.DocumentFields.boolean
import io.github.junekim0007.cryptobench.document.DocumentFields.number
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalBoolean
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalNumber
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalSection
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalSections
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalString
import io.github.junekim0007.cryptobench.document.DocumentFields.section
import io.github.junekim0007.cryptobench.document.DocumentFields.sections
import io.github.junekim0007.cryptobench.document.DocumentFields.string

object TrialSource : DocumentReader<TrialView> {

    override val schemaVersion: Int = 3

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
        // required: a trial written before the keystore trial is refused; an absent section (no keystore on that runtime) has no rows
        val keystore = optionalSections(section(document, "keystore"), "rows").map { keystoreRow(it) }
        return TrialView(number(document, "capturedAtMillis").toLong(), entries, optionalNumber(document, "defaultRunInputSize")?.toInt(), keystore)
    }

    private fun keystoreRow(document: Map<String, Any>): KeystoreRow = KeystoreRow(
        provider = string(document, "provider"),
        type = string(document, "type"),
        algorithm = string(document, "algorithm"),
        backing = string(document, "backing"),
        keySize = optionalNumber(document, "keySize")?.toInt(),
        curve = optionalString(document, "curve"),
        supported = boolean(document, "supported"),
        error = optionalString(document, "error"),
    )

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
