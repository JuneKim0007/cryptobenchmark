package io.github.junekim0007.cryptobench.contract.capture

import io.github.junekim0007.cryptobench.document.SchemaVersion
import io.github.junekim0007.cryptobench.document.versioned.DocumentReader
import io.github.junekim0007.cryptobench.document.versioned.YamlFiles
import io.github.junekim0007.cryptobench.document.DocumentFields.number
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalSection
import io.github.junekim0007.cryptobench.document.DocumentFields.sectionsIfKeyPresent
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalStrings
import io.github.junekim0007.cryptobench.document.DocumentFields.section
import io.github.junekim0007.cryptobench.document.DocumentFields.sections
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalString
import io.github.junekim0007.cryptobench.document.DocumentFields.string
import java.io.File

object CaptureDocument : DocumentReader<CapturedEnvironment> {

    override val schemaVersion = CapturedEnvironment.SCHEMA_VERSION

    private const val CAPTURED_AT_MILLIS = "capturedAtMillis"
    private const val DEVICE_CLOCK_MILLIS = "deviceClockMillis"
    internal const val RUNTIME = "runtime"
    internal const val PROVIDERS = "providers"

    private const val NAME = "name"
    private const val VERSION = "version"
    private const val PRECEDENCE = "precedence"
    internal const val ORIGIN = "origin"
    private const val ARTIFACT = "artifact"
    private const val SERVICES = "services"

    private const val TYPE = "type"
    private const val ALGORITHM = "algorithm"
    private const val CLASS_NAME = "className"
    private const val ALIASES = "aliases"
    private const val ATTRIBUTES = "attributes"

    fun of(environment: CapturedEnvironment): Map<String, Any> = linkedMapOf(
        SchemaVersion.FIELD to environment.schemaVersion,
        CAPTURED_AT_MILLIS to environment.capturedAtMillis,
        DEVICE_CLOCK_MILLIS to environment.deviceClockMillis,
        RUNTIME to RuntimeDocument.of(environment.runtime),
        PROVIDERS to environment.providers.map { providerDocument(it) },
    )

    fun read(file: File): CapturedEnvironment = YamlFiles().readOnly(file, this).read()

    override fun parse(document: Map<String, Any>): CapturedEnvironment {
        val schemaVersion = number(document, SchemaVersion.FIELD).toInt()
        return CapturedEnvironment(
            runtime = RuntimeDocument.parse(section(document, RUNTIME)),
            providers = sections(document, PROVIDERS).map { providerEntry(it) },
            capturedAtMillis = number(document, CAPTURED_AT_MILLIS).toLong(),
            deviceClockMillis = number(document, DEVICE_CLOCK_MILLIS).toLong(),
            schemaVersion = schemaVersion,
        )
    }

    private fun providerDocument(provider: ProviderEntry): Map<String, Any> {
        val document = linkedMapOf<String, Any>(
            NAME to provider.name,
            VERSION to provider.version,
            PRECEDENCE to provider.precedence,
            ORIGIN to provider.origin.key,
            SERVICES to provider.services.map { serviceDocument(it) },
        )
        if (provider.artifact.isNotEmpty()) {
            document[ARTIFACT] = provider.artifact
        }
        return document
    }

    private fun providerEntry(document: Map<String, Any>): ProviderEntry = ProviderEntry(
        name = string(document, NAME),
        precedence = number(document, PRECEDENCE).toInt(),
        version = string(document, VERSION),
        services = sections(document, SERVICES).map { serviceEntry(it) },
        origin = ProviderOrigin.of(string(document, ORIGIN)),
        artifact = optionalString(document, ARTIFACT),
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
