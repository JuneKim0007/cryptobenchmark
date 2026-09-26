package io.github.junekim0007.cryptobench.preparation.device

import io.github.junekim0007.cryptobench.preparation.device.dto.CapturedDevice
import io.github.junekim0007.cryptobench.preparation.device.dto.CapturedProvider
import io.github.junekim0007.cryptobench.preparation.device.dto.CapturedService
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields.number
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields.optionalStrings
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields.optionalSections
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields.sections
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields.string
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFile
import java.io.File

object CaptureFile {

    const val SUPPORTED_SCHEMA_VERSION = 1

    private const val SCHEMA_NAME = "capture"

    fun read(file: File): CapturedDevice =
        device(DocumentFile.read(file, SCHEMA_NAME, SUPPORTED_SCHEMA_VERSION))

    fun read(fileName: String, text: String): CapturedDevice =
        device(DocumentFile.read(fileName, text, SCHEMA_NAME, SUPPORTED_SCHEMA_VERSION))

    private fun device(document: Map<String, Any>): CapturedDevice = CapturedDevice(
        capturedAtMillis = number(document, "capturedAtMillis").toLong(),
        providers = sections(document, "providers").map { provider ->
            CapturedProvider(
                name = string(provider, "name"),
                precedence = number(provider, "precedence").toInt(),
                services = optionalSections(provider, "services").map { service ->
                    CapturedService(
                        type = string(service, "type"),
                        algorithm = string(service, "algorithm"),
                        aliases = optionalStrings(service, "aliases"),
                    )
                },
            )
        },
    )
}
