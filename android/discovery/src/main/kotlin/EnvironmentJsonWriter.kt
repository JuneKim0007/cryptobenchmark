package io.github.junekim0007.cryptobench.discovery

import io.github.junekim0007.cryptobench.discovery.capture.CapturedEnvironment
import io.github.junekim0007.cryptobench.discovery.capture.ProviderEntry
import io.github.junekim0007.cryptobench.discovery.capture.RuntimeInfo
import io.github.junekim0007.cryptobench.discovery.capture.ServiceEntry

import org.json.JSONArray
import org.json.JSONObject
import java.io.File

/** Turns a capture into JSON. org.json because Android ships it; the probe never sees this class. */
class EnvironmentJsonWriter {

    fun toJson(environment: CapturedEnvironment): JSONObject = JSONObject().apply {
        put("schemaVersion", environment.schemaVersion)
        put("capturedAtMillis", environment.capturedAtMillis)
        put("runtime", runtime(environment.runtime))
        put("providers", JSONArray().apply {
            environment.providers.forEach { put(provider(it)) }
        })
    }

    fun write(environment: CapturedEnvironment, target: File) {
        target.parentFile?.let {
            if (!it.exists() && !it.mkdirs()) {
                throw java.io.IOException("cannot create ${it.absolutePath}")
            }
        }
        target.writeText(toJson(environment).toString(2), Charsets.UTF_8)
    }

    private fun runtime(runtime: RuntimeInfo): JSONObject = JSONObject().apply {
        put("model", runtime.model)
        put("manufacturer", runtime.manufacturer)
        put("hardware", runtime.hardware)
        put("sdkInt", runtime.sdkInt)
        put("release", runtime.release)
        put("javaVersion", runtime.javaVersion)
    }

    private fun provider(provider: ProviderEntry): JSONObject = JSONObject().apply {
        put("name", provider.name)
        put("version", provider.version)
        put("precedence", provider.precedence)
        put("info", provider.info)
        put("usable", provider.usable)
        put("services", JSONArray().apply {
            provider.services.forEach { put(service(it)) }
        })
        if (provider.unresolvedAliases.isNotEmpty()) {
            put("unresolvedAliases", JSONObject().apply {
                provider.unresolvedAliases.forEach { (alias, target) -> put(alias, target) }
            })
        }
    }

    private fun service(service: ServiceEntry): JSONObject = JSONObject().apply {
        put("type", service.type)
        put("algorithm", service.algorithm)
        put("className", service.className)
        if (service.aliases.isNotEmpty()) {
            put("aliases", JSONArray(service.aliases))
        }
        val attributes = service.attributes
        if (!attributes.isEmpty) {
            put("attributes", JSONObject().apply {
                attributes.document().forEach { (name, value) ->
                    put(name, if (value is List<*>) JSONArray(value) else value)
                }
            })
        }
    }
}
