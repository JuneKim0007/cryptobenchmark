package io.github.junekim0007.cryptobench.discovery.write

import io.github.junekim0007.cryptobench.discovery.contract.CapturedEnvironment
import java.io.File

class EnvironmentYamlWriter(
    private val directory: ProbeDirectory,
    private val codec: YamlCodec = YamlCodec(),
) {

    fun toDocument(environment: CapturedEnvironment): Map<String, Any> = CaptureDocument.of(environment)

    fun toYaml(environment: CapturedEnvironment): String = codec.dump(toDocument(environment))

    fun fileName(capturedAtMillis: Long): String = ProbeFileName.of("probe", capturedAtMillis)

    fun write(environment: CapturedEnvironment): File =
        directory.create(fileName(environment.capturedAtMillis), toYaml(environment))
}
