package io.github.junekim0007.cryptobench.discovery.write

import io.github.junekim0007.cryptobench.discovery.contract.CapturedEnvironment
import org.yaml.snakeyaml.DumperOptions
import org.yaml.snakeyaml.Yaml
import java.io.File
import java.io.IOException
import java.time.Instant
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter

class ProviderClassNameWriter {

    private val yaml = Yaml(DumperOptions().apply {
        defaultFlowStyle = DumperOptions.FlowStyle.BLOCK
        indent = 2
    })

    fun toDocument(environment: CapturedEnvironment): Map<String, List<String>> =
        environment.providers.associateTo(LinkedHashMap()) { provider ->
            provider.name to provider.services.map { it.className }.filter { it.isNotBlank() }.distinct().sorted()
        }

    fun toYaml(environment: CapturedEnvironment): String = yaml.dump(toDocument(environment))

    fun fileName(capturedAtMillis: Long): String =
        "probe_classes_" + FILE_STAMP.format(Instant.ofEpochMilli(capturedAtMillis)) + ".yaml"

    fun write(environment: CapturedEnvironment, directory: File): File {
        if (!directory.exists() && !directory.mkdirs()) {
            throw IOException("cannot create ${directory.absolutePath}")
        }
        val target = File(directory, fileName(environment.capturedAtMillis))
        target.writeText(toYaml(environment), Charsets.UTF_8)
        return target
    }

    companion object {
        private val FILE_STAMP: DateTimeFormatter =
            DateTimeFormatter.ofPattern("yyyyMMdd'T'HHmmss'Z'").withZone(ZoneOffset.UTC)
    }
}
