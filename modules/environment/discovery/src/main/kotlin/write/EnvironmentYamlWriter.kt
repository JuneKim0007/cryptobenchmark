package io.github.junekim0007.cryptobench.discovery.write

import io.github.junekim0007.cryptobench.discovery.contract.CapturedEnvironment
import java.io.File

class EnvironmentYamlWriter {

    fun toDocument(environment: CapturedEnvironment): Map<String, Any> = CaptureDocument.of(environment)

    fun toYaml(environment: CapturedEnvironment): String = YamlDocument.dump(toDocument(environment))

    fun fileName(capturedAtMillis: Long): String = ProbeFile.name("probe", capturedAtMillis)

    fun write(environment: CapturedEnvironment, directory: File): File =
        ProbeFile.write(directory, fileName(environment.capturedAtMillis), toYaml(environment))
}
