package io.github.junekim0007.cryptobench.discovery.write

import io.github.junekim0007.cryptobench.discovery.contract.CapturedEnvironment
import io.github.junekim0007.cryptobench.discovery.contract.ProviderEntry
import io.github.junekim0007.cryptobench.discovery.contract.RuntimeInfo
import io.github.junekim0007.cryptobench.discovery.contract.ServiceEntry
import org.yaml.snakeyaml.DumperOptions
import org.yaml.snakeyaml.Yaml
import java.io.File
import java.io.IOException
import java.time.Instant
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter

class EnvironmentYamlWriter {

    private val yaml = Yaml(DumperOptions().apply {
        defaultFlowStyle = DumperOptions.FlowStyle.BLOCK
        indent = 2
        isPrettyFlow = true
    })

    fun toDocument(environment: CapturedEnvironment): Map<String, Any> = linkedMapOf(
        "schemaVersion" to environment.schemaVersion,
        "capturedAtMillis" to environment.capturedAtMillis,
        "runtime" to runtime(environment.runtime),
        "providers" to environment.providers.map { provider(it) },
    )

    fun toYaml(environment: CapturedEnvironment): String = yaml.dump(toDocument(environment))

    fun fileName(capturedAtMillis: Long): String =
        "probe_" + FILE_STAMP.format(Instant.ofEpochMilli(capturedAtMillis)) + ".yaml"

    fun write(environment: CapturedEnvironment, directory: File): File {
        if (!directory.exists() && !directory.mkdirs()) {
            throw IOException("cannot create ${directory.absolutePath}")
        }
        val target = File(directory, fileName(environment.capturedAtMillis))
        target.writeText(toYaml(environment), Charsets.UTF_8)
        return target
    }

    private fun runtime(runtime: RuntimeInfo): Map<String, Any> = linkedMapOf(
        "model" to runtime.model,
        "manufacturer" to runtime.manufacturer,
        "hardware" to runtime.hardware,
        "sdkInt" to runtime.sdkInt,
        "release" to runtime.release,
        "javaVersion" to runtime.javaVersion,
    )

    private fun provider(provider: ProviderEntry): Map<String, Any> {
        val document = linkedMapOf<String, Any>(
            "name" to provider.name,
            "version" to provider.version,
            "precedence" to provider.precedence,
            "info" to provider.info,
            "usable" to provider.usable,
            "services" to provider.services.map { service(it) },
        )
        if (provider.unresolvedAliases.isNotEmpty()) {
            document["unresolvedAliases"] = provider.unresolvedAliases.map { alias ->
                linkedMapOf("type" to alias.type, "alias" to alias.name, "target" to alias.target)
            }
        }
        return document
    }

    private fun service(service: ServiceEntry): Map<String, Any> {
        val document = linkedMapOf<String, Any>(
            "type" to service.type,
            "algorithm" to service.algorithm,
            "className" to service.className,
        )
        if (service.aliases.isNotEmpty()) {
            document["aliases"] = service.aliases
        }
        if (!service.attributes.isEmpty) {
            document["attributes"] = LinkedHashMap(service.attributes.document())
        }
        return document
    }

    companion object {
        private val FILE_STAMP: DateTimeFormatter =
            DateTimeFormatter.ofPattern("yyyyMMdd'T'HHmmss'Z'").withZone(ZoneOffset.UTC)
    }
}
