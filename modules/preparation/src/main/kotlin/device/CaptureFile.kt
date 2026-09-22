package io.github.junekim0007.cryptobench.preparation.device

import io.github.junekim0007.cryptobench.preparation.device.dto.CapturedDevice
import io.github.junekim0007.cryptobench.preparation.device.dto.CapturedProvider
import io.github.junekim0007.cryptobench.preparation.device.dto.CapturedService
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields.number
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields.optionalStrings
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields.optionalSections
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields.sections
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields.string
import io.github.junekim0007.cryptobench.preparation.shared.YamlCodec
import org.yaml.snakeyaml.error.YAMLException
import java.io.File

object CaptureFile {

    const val SUPPORTED_SCHEMA_VERSION = 1

    fun read(file: File): CapturedDevice {
        require(file.isFile) { "missing_file: ${file.path}" }
        return read(file.name, file.readText())
    }

    fun read(fileName: String, text: String): CapturedDevice {
        val document = try {
            YamlCodec().load(text)
        } catch (failure: YAMLException) {
            throw IllegalArgumentException("unreadable_yaml: $fileName: ${failure.message}", failure)
        }
        val schemaVersion = number(document, "schemaVersion").toInt()
        require(schemaVersion == SUPPORTED_SCHEMA_VERSION) {
            "unsupported_capture_schema: $fileName: $schemaVersion, this build reads $SUPPORTED_SCHEMA_VERSION"
        }
        return CapturedDevice(
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
}
