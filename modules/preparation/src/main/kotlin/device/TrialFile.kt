package io.github.junekim0007.cryptobench.preparation.device

import io.github.junekim0007.cryptobench.preparation.device.dto.TrialledDevice
import io.github.junekim0007.cryptobench.preparation.device.dto.TrialledService
import io.github.junekim0007.cryptobench.preparation.device.dto.TrialledTransformation
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields.boolean
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields.number
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields.optionalSections
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields.optionalString
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields.sections
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields.string
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFile
import java.io.File

object TrialFile {

    const val SUPPORTED_SCHEMA_VERSION = 2

    private const val SCHEMA_NAME = "trial"

    fun read(file: File): TrialledDevice =
        device(DocumentFile.read(file, SCHEMA_NAME, SUPPORTED_SCHEMA_VERSION))

    fun read(fileName: String, text: String): TrialledDevice =
        device(DocumentFile.read(fileName, text, SCHEMA_NAME, SUPPORTED_SCHEMA_VERSION))

    private fun device(document: Map<String, Any>): TrialledDevice = TrialledDevice(
        capturedAtMillis = number(document, "capturedAtMillis").toLong(),
        services = sections(document, "services").map { service ->
            TrialledService(
                provider = string(service, "provider"),
                type = string(service, "type"),
                algorithm = string(service, "algorithm"),
                instantiates = boolean(service, "instantiates"),
                error = optionalString(service, "error"),
                transformations = optionalSections(service, "transformations").map { transformation ->
                    TrialledTransformation(
                        name = string(transformation, "name"),
                        instantiates = boolean(transformation, "instantiates"),
                        error = optionalString(transformation, "error"),
                    )
                },
            )
        },
    )
}
