package io.github.junekim0007.cryptobench.preparation.device

import io.github.junekim0007.cryptobench.preparation.device.dto.CapturedDevice
import io.github.junekim0007.cryptobench.preparation.device.dto.CapturedProvider
import io.github.junekim0007.cryptobench.preparation.device.dto.CapturedService
import io.github.junekim0007.cryptobench.document.DocumentFields.number
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalStrings
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalSections
import io.github.junekim0007.cryptobench.document.DocumentFields.sections
import io.github.junekim0007.cryptobench.document.DocumentFields.sectionOrEmpty
import io.github.junekim0007.cryptobench.document.DocumentFields.string
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFile
import java.io.File

object CaptureFile {

    const val SUPPORTED_SCHEMA_VERSION = 1


    fun read(file: File): CapturedDevice =
        device(DocumentFile.read(file, SUPPORTED_SCHEMA_VERSION))

    fun read(fileName: String, text: String): CapturedDevice =
        device(DocumentFile.read(fileName, text, SUPPORTED_SCHEMA_VERSION))

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
        sdkInt = sdkInt(document),
        platform = sdkInt(document)?.let { "android-$it" } ?: sectionOrEmpty(document, "runtime")["javaVersion"]?.toString()?.substringBefore('.')?.takeIf { it.isNotEmpty() }?.let { "jdk-$it" },
    )

    private fun sdkInt(document: Map<String, Any>): Int? = (sectionOrEmpty(document, "runtime")["sdkInt"] as? Number)?.toInt()?.takeIf { it > 0 }
}
