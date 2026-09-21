package io.github.junekim0007.cryptobench.discovery.write

import io.github.junekim0007.cryptobench.discovery.contract.CapturedEnvironment
import io.github.junekim0007.cryptobench.discovery.contract.ProviderEntry
import io.github.junekim0007.cryptobench.discovery.contract.RuntimeInfo
import io.github.junekim0007.cryptobench.discovery.contract.ServiceEntry

object CaptureDocument {

    const val SCHEMA_VERSION = "schemaVersion"
    const val CAPTURED_AT_MILLIS = "capturedAtMillis"
    const val RUNTIME = "runtime"
    const val PROVIDERS = "providers"

    const val MODEL = "model"
    const val MANUFACTURER = "manufacturer"
    const val HARDWARE = "hardware"
    const val SDK_INT = "sdkInt"
    const val RELEASE = "release"
    const val JAVA_VERSION = "javaVersion"

    const val NAME = "name"
    const val VERSION = "version"
    const val PRECEDENCE = "precedence"
    const val INFO = "info"
    const val USABLE = "usable"
    const val SERVICES = "services"
    const val UNRESOLVED_ALIASES = "unresolvedAliases"

    const val TYPE = "type"
    const val ALGORITHM = "algorithm"
    const val CLASS_NAME = "className"
    const val ALIASES = "aliases"
    const val ATTRIBUTES = "attributes"
    const val ALIAS = "alias"
    const val TARGET = "target"

    fun of(environment: CapturedEnvironment): Map<String, Any> = linkedMapOf(
        SCHEMA_VERSION to environment.schemaVersion,
        CAPTURED_AT_MILLIS to environment.capturedAtMillis,
        RUNTIME to runtime(environment.runtime),
        PROVIDERS to environment.providers.map { provider(it) },
    )

    private fun runtime(runtime: RuntimeInfo): Map<String, Any> = linkedMapOf(
        MODEL to runtime.model,
        MANUFACTURER to runtime.manufacturer,
        HARDWARE to runtime.hardware,
        SDK_INT to runtime.sdkInt,
        RELEASE to runtime.release,
        JAVA_VERSION to runtime.javaVersion,
    )

    private fun provider(provider: ProviderEntry): Map<String, Any> {
        val document = linkedMapOf<String, Any>(
            NAME to provider.name,
            VERSION to provider.version,
            PRECEDENCE to provider.precedence,
            INFO to provider.info,
            USABLE to provider.usable,
            SERVICES to provider.services.map { service(it) },
        )
        if (provider.unresolvedAliases.isNotEmpty()) {
            document[UNRESOLVED_ALIASES] = provider.unresolvedAliases.map { alias ->
                linkedMapOf(TYPE to alias.type, ALIAS to alias.name, TARGET to alias.target)
            }
        }
        return document
    }

    private fun service(service: ServiceEntry): Map<String, Any> {
        val document = linkedMapOf<String, Any>(
            TYPE to service.type,
            ALGORITHM to service.algorithm,
            CLASS_NAME to service.className,
        )
        if (service.aliases.isNotEmpty()) {
            document[ALIASES] = service.aliases
        }
        if (!service.attributes.isEmpty) {
            document[ATTRIBUTES] = LinkedHashMap(service.attributes.document())
        }
        return document
    }
}
