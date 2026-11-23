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

    private const val MODEL = "model"
    private const val MANUFACTURER = "manufacturer"
    private const val HARDWARE = "hardware"
    private const val SDK_INT = "sdkInt"
    private const val RELEASE = "release"
    private const val JAVA_VERSION = "javaVersion"
    internal const val DEFAULT_KEY_SIZE_PROPERTY = "defaultKeySizeProperty"
    internal const val FINGERPRINT = "fingerprint"
    private const val JAVA_VENDOR = "javaVendor"
    private const val JAVA_RUNTIME_VERSION = "javaRuntimeVersion"
    private const val OS_NAME = "osName"
    private const val OS_ARCH = "osArch"

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
        RUNTIME to runtimeDocument(environment.runtime),
        PROVIDERS to environment.providers.map { providerDocument(it) },
    )

    fun read(file: File): CapturedEnvironment = YamlFiles().readOnly(file, this).read()

    override fun parse(document: Map<String, Any>): CapturedEnvironment {
        val schemaVersion = number(document, SchemaVersion.FIELD).toInt()
        return CapturedEnvironment(
            runtime = runtimeEntry(section(document, RUNTIME)),
            providers = sections(document, PROVIDERS).map { providerEntry(it) },
            capturedAtMillis = number(document, CAPTURED_AT_MILLIS).toLong(),
            deviceClockMillis = number(document, DEVICE_CLOCK_MILLIS).toLong(),
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
        FINGERPRINT to runtime.fingerprint,
        JAVA_VENDOR to runtime.javaVendor,
        JAVA_RUNTIME_VERSION to runtime.javaRuntimeVersion,
        OS_NAME to runtime.osName,
        OS_ARCH to runtime.osArch,
    )

    private fun runtimeEntry(document: Map<String, Any>): RuntimeInfo = RuntimeInfo(
        model = string(document, MODEL),
        manufacturer = string(document, MANUFACTURER),
        hardware = string(document, HARDWARE),
        sdkInt = number(document, SDK_INT).toInt(),
        release = string(document, RELEASE),
        javaVersion = string(document, JAVA_VERSION),
        defaultKeySizeProperty = string(document, DEFAULT_KEY_SIZE_PROPERTY),
        fingerprint = string(document, FINGERPRINT),
        javaVendor = string(document, JAVA_VENDOR),
        javaRuntimeVersion = string(document, JAVA_RUNTIME_VERSION),
        osName = string(document, OS_NAME),
        osArch = string(document, OS_ARCH),
    )

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
