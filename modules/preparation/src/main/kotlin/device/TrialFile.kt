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
import io.github.junekim0007.cryptobench.preparation.shared.YamlCodec
import org.yaml.snakeyaml.error.YAMLException
import java.io.File

object TrialFile {

    const val SUPPORTED_SCHEMA_VERSION = 2

    fun read(file: File): TrialledDevice {
        require(file.isFile) { "missing_file: ${file.path}" }
        return read(file.name, file.readText())
    }

    fun read(fileName: String, text: String): TrialledDevice {
        val document = try {
            YamlCodec().load(text)
        } catch (failure: YAMLException) {
            throw IllegalArgumentException("unreadable_yaml: $fileName: ${failure.message}", failure)
        }
        val schemaVersion = number(document, "schemaVersion").toInt()
        require(schemaVersion == SUPPORTED_SCHEMA_VERSION) {
            "unsupported_trial_schema: $fileName: $schemaVersion, this build reads $SUPPORTED_SCHEMA_VERSION"
        }
        return TrialledDevice(
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
}
