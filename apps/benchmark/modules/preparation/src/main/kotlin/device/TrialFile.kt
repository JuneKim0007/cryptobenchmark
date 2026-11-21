package io.github.junekim0007.cryptobench.preparation.device

import io.github.junekim0007.cryptobench.document.DocumentFields.boolean
import io.github.junekim0007.cryptobench.document.DocumentFields.number
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalSections
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalString
import io.github.junekim0007.cryptobench.document.DocumentFields.sectionOrEmpty
import io.github.junekim0007.cryptobench.document.DocumentFields.sections
import io.github.junekim0007.cryptobench.document.DocumentFields.string
import io.github.junekim0007.cryptobench.preparation.device.dto.TrialledDevice
import io.github.junekim0007.cryptobench.preparation.device.dto.TrialledService
import io.github.junekim0007.cryptobench.preparation.device.dto.TrialledTransformation
import io.github.junekim0007.cryptobench.document.versioned.DocumentReader
import io.github.junekim0007.cryptobench.document.versioned.YamlFiles
import java.io.File

object TrialFile : DocumentReader<TrialledDevice> {

    const val SUPPORTED_SCHEMA_VERSION = 3

    override val schemaVersion = SUPPORTED_SCHEMA_VERSION

    fun read(file: File): TrialledDevice = YamlFiles().readOnly(file, this).read()

    fun read(fileName: String, text: String): TrialledDevice = YamlFiles().readOnly(File(fileName), this).read(text)

    override fun parse(document: Map<String, Any>): TrialledDevice = TrialledDevice(
        capturedAtMillis = number(document, "capturedAtMillis").toLong(),
        services = sections(document, "services").map { service ->
            TrialledService(
                provider = string(service, "provider"),
                type = string(service, "type"),
                algorithm = string(service, "algorithm"),
                instantiates = boolean(service, "instantiates"),
                error = optionalString(service, "error"),
                keyAlgorithm = measuredKeyAlgorithm(service),
                fixedKeySize = fixedKeySize(service),
                transformations = optionalSections(service, "transformations").map { transformation ->
                    TrialledTransformation(
                        name = string(transformation, "name"),
                        instantiates = boolean(transformation, "instantiates"),
                        error = optionalString(transformation, "error"),
                        keyAlgorithm = measuredKeyAlgorithm(transformation),
                        fixedKeySize = fixedKeySize(transformation),
                    )
                },
            )
        },
    )

    private fun measuredKeyAlgorithm(trialled: Map<String, Any>): String =
        optionalString(sectionOrEmpty(trialled, "defaultRun"), "keyAlgorithm")

    private fun fixedKeySize(trialled: Map<String, Any>): Int? =
        (sectionOrEmpty(trialled, "defaultRun")["fixedKeySize"] as? Number)?.toInt()
}
