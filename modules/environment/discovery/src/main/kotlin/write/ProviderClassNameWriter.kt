package io.github.junekim0007.cryptobench.discovery.write

import io.github.junekim0007.cryptobench.discovery.contract.CapturedEnvironment
import java.io.File

class ProviderClassNameWriter {

    fun toDocument(environment: CapturedEnvironment): Map<String, List<String>> =
        environment.providers.associateTo(LinkedHashMap()) { provider ->
            provider.name to provider.services.map { it.className }.filter { it.isNotBlank() }.distinct().sorted()
        }

    fun toYaml(environment: CapturedEnvironment): String = YamlDocument.dump(toDocument(environment))

    fun fileName(capturedAtMillis: Long): String = ProbeFile.name("probe_classes", capturedAtMillis)

    fun write(environment: CapturedEnvironment, directory: File): File =
        ProbeFile.write(directory, fileName(environment.capturedAtMillis), toYaml(environment))
}
