package io.github.junekim0007.cryptobench.discovery.write

import io.github.junekim0007.cryptobench.discovery.contract.CapturedEnvironment
import java.io.File

class ProviderClassNameWriter(
    private val directory: ProbeDirectory,
    private val codec: YamlCodec = YamlCodec(),
) {

    fun toDocument(environment: CapturedEnvironment): Map<String, List<String>> =
        environment.providers.associateTo(LinkedHashMap()) { provider ->
            provider.name to provider.services.map { it.className }.filter { it.isNotBlank() }.distinct().sorted()
        }

    fun toYaml(environment: CapturedEnvironment): String = codec.dump(toDocument(environment))

    fun fileName(capturedAtMillis: Long): String = ProbeFileName.of("probe_classes", capturedAtMillis)

    fun write(environment: CapturedEnvironment): File =
        directory.create(fileName(environment.capturedAtMillis), toYaml(environment))
}
