package io.github.junekim0007.cryptobench.preparation.device

import io.github.junekim0007.cryptobench.preparation.device.dto.CapturedDevice
import io.github.junekim0007.cryptobench.preparation.device.dto.CapturedProvider
import io.github.junekim0007.cryptobench.preparation.device.dto.CapturedService
import io.github.junekim0007.cryptobench.document.DocumentFields.number
import io.github.junekim0007.cryptobench.document.catalogue.CatalogueOverlays
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalStrings
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalSections
import io.github.junekim0007.cryptobench.document.DocumentFields.sections
import io.github.junekim0007.cryptobench.document.DocumentFields.sectionOrEmpty
import io.github.junekim0007.cryptobench.document.DocumentFields.string
import io.github.junekim0007.cryptobench.document.versioned.DocumentReader
import io.github.junekim0007.cryptobench.document.versioned.YamlFiles
import java.io.File

object CaptureFile : DocumentReader<CapturedDevice> {

    const val SUPPORTED_SCHEMA_VERSION = 1

    override val schemaVersion = SUPPORTED_SCHEMA_VERSION

    fun read(file: File): CapturedDevice = YamlFiles().readOnly(file, this).read()

    fun read(fileName: String, text: String): CapturedDevice = YamlFiles().readOnly(File(fileName), this).read(text)

    override fun parse(document: Map<String, Any>): CapturedDevice = CapturedDevice(
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
        platform = CatalogueOverlays.platform(sdkInt(document), sectionOrEmpty(document, "runtime")["javaVersion"]?.toString()),
    )

    private fun sdkInt(document: Map<String, Any>): Int? = (sectionOrEmpty(document, "runtime")["sdkInt"] as? Number)?.toInt()?.takeIf { it > 0 }
}
