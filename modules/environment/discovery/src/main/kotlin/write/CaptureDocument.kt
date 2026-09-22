package io.github.junekim0007.cryptobench.discovery.write

import io.github.junekim0007.cryptobench.discovery.contract.AliasEntry
import io.github.junekim0007.cryptobench.discovery.contract.CapturedEnvironment
import io.github.junekim0007.cryptobench.discovery.contract.ProviderEntry
import io.github.junekim0007.cryptobench.discovery.contract.RuntimeInfo
import io.github.junekim0007.cryptobench.discovery.contract.ServiceAttributes
import io.github.junekim0007.cryptobench.discovery.contract.ServiceEntry
import io.github.junekim0007.cryptobench.discovery.write.DocumentFields.number
import io.github.junekim0007.cryptobench.discovery.write.DocumentFields.optionalSection
import io.github.junekim0007.cryptobench.discovery.write.DocumentFields.optionalSections
import io.github.junekim0007.cryptobench.discovery.write.DocumentFields.optionalStrings
import io.github.junekim0007.cryptobench.discovery.write.DocumentFields.section
import io.github.junekim0007.cryptobench.discovery.write.DocumentFields.sections
import io.github.junekim0007.cryptobench.discovery.write.DocumentFields.optionalString
import io.github.junekim0007.cryptobench.discovery.write.DocumentFields.string

object CaptureDocument {

    internal const val SCHEMA_VERSION = "schemaVersion"
    private const val CAPTURED_AT_MILLIS = "capturedAtMillis"
    internal const val RUNTIME = "runtime"
    internal const val PROVIDERS = "providers"

    private const val MODEL = "model"
    private const val MANUFACTURER = "manufacturer"
    private const val HARDWARE = "hardware"
    private const val SDK_INT = "sdkInt"
    private const val RELEASE = "release"
    private const val JAVA_VERSION = "javaVersion"
    internal const val DEFAULT_KEY_SIZE_PROPERTY = "defaultKeySizeProperty"

    private const val NAME = "name"
    private const val VERSION = "version"
    private const val PRECEDENCE = "precedence"
    private const val INFO = "info"
    private const val USABLE = "usable"
    private const val SERVICES = "services"
    private const val UNRESOLVED_ALIASES = "unresolvedAliases"

    private const val TYPE = "type"
    private const val ALGORITHM = "algorithm"
    private const val CLASS_NAME = "className"
    private const val ALIASES = "aliases"
    private const val ATTRIBUTES = "attributes"
    private const val ALIAS = "alias"
    private const val TARGET = "target"

    fun of(environment: CapturedEnvironment): Map<String, Any> = linkedMapOf(
        SCHEMA_VERSION to environment.schemaVersion,
        CAPTURED_AT_MILLIS to environment.capturedAtMillis,
        RUNTIME to runtimeDocument(environment.runtime),
        PROVIDERS to environment.providers.map { providerDocument(it) },
    )

    fun parse(document: Map<String, Any>): CapturedEnvironment {
        val schemaVersion = number(document, SCHEMA_VERSION).toInt()
        require(schemaVersion == CapturedEnvironment.SCHEMA_VERSION) {
            "unsupported_schema_version: $schemaVersion, this build reads ${CapturedEnvironment.SCHEMA_VERSION}"
        }
        return CapturedEnvironment(
            runtime = runtimeEntry(section(document, RUNTIME)),
            providers = sections(document, PROVIDERS).map { providerEntry(it) },
            capturedAtMillis = number(document, CAPTURED_AT_MILLIS).toLong(),
            schemaVersion = schemaVersion,
        )
    }

    private fun runtimeDocument(runtime: RuntimeInfo): Map<String, Any> = linkedMapOf(
        MODEL to runtime.model,
        MANUFACTURER to runtime.manufacturer,
        HARDWARE to runtime.hardware,
        SDK_INT to runtime.sdkInt,
        RELEASE to runtime.release,
        JAVA_VERSION to runtime.javaVersion,
        DEFAULT_KEY_SIZE_PROPERTY to runtime.defaultKeySizeProperty,
    )

    private fun runtimeEntry(document: Map<String, Any>): RuntimeInfo = RuntimeInfo(
        model = string(document, MODEL),
        manufacturer = string(document, MANUFACTURER),
        hardware = string(document, HARDWARE),
        sdkInt = number(document, SDK_INT).toInt(),
        release = string(document, RELEASE),
        javaVersion = string(document, JAVA_VERSION),
        defaultKeySizeProperty = optionalString(document, DEFAULT_KEY_SIZE_PROPERTY),
    )

    private fun providerDocument(provider: ProviderEntry): Map<String, Any> {
        val document = linkedMapOf<String, Any>(
            NAME to provider.name,
            VERSION to provider.version,
            PRECEDENCE to provider.precedence,
            INFO to provider.info,
            USABLE to provider.usable,
            SERVICES to provider.services.map { serviceDocument(it) },
        )
        if (provider.unresolvedAliases.isNotEmpty()) {
            document[UNRESOLVED_ALIASES] = provider.unresolvedAliases.map { alias ->
                linkedMapOf(TYPE to alias.type, ALIAS to alias.name, TARGET to alias.target)
            }
        }
        return document
    }

    private fun providerEntry(document: Map<String, Any>): ProviderEntry = ProviderEntry(
        name = string(document, NAME),
        precedence = number(document, PRECEDENCE).toInt(),
        version = string(document, VERSION),
        info = string(document, INFO),
        services = sections(document, SERVICES).map { serviceEntry(it) },
        unresolvedAliases = optionalSections(document, UNRESOLVED_ALIASES).map { aliasEntry(it) },
    )

    private fun aliasEntry(document: Map<String, Any>): AliasEntry = AliasEntry(
        type = string(document, TYPE),
        name = string(document, ALIAS),
        target = string(document, TARGET),
    )

    private fun serviceDocument(service: ServiceEntry): Map<String, Any> {
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

    private fun serviceEntry(document: Map<String, Any>): ServiceEntry = ServiceEntry(
        type = string(document, TYPE),
        algorithm = string(document, ALGORITHM),
        className = string(document, CLASS_NAME),
        aliases = optionalStrings(document, ALIASES),
        attributes = ServiceAttributes.of(optionalSection(document, ATTRIBUTES)),
    )
}
