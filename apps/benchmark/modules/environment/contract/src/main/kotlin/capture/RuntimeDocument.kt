package io.github.junekim0007.cryptobench.contract.capture

import io.github.junekim0007.cryptobench.document.DocumentFields.number
import io.github.junekim0007.cryptobench.document.DocumentFields.string

/** A capture's runtime section: its key names, written and read. */
object RuntimeDocument {

    private const val MODEL = "model"
    private const val MANUFACTURER = "manufacturer"
    private const val HARDWARE = "hardware"
    private const val SDK_INT = "sdkInt"
    private const val RELEASE = "release"
    private const val JAVA_VERSION = "javaVersion"
    private const val DEFAULT_KEY_SIZE_PROPERTY = "defaultKeySizeProperty"
    private const val FINGERPRINT = "fingerprint"
    private const val JAVA_VENDOR = "javaVendor"
    private const val JAVA_RUNTIME_VERSION = "javaRuntimeVersion"
    private const val OS_NAME = "osName"
    private const val OS_ARCH = "osArch"

    private val HOST = listOf(JAVA_VERSION, DEFAULT_KEY_SIZE_PROPERTY, JAVA_VENDOR, JAVA_RUNTIME_VERSION, OS_NAME, OS_ARCH)

    fun of(runtime: RuntimeInfo): Map<String, Any> = linkedMapOf(
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

    // the keys a host benchmark.json carries, in this order
    fun host(runtime: RuntimeInfo): Map<String, String> = of(runtime).let { all -> HOST.associateWith { all.getValue(it).toString() } }

    fun parse(document: Map<String, Any>): RuntimeInfo = RuntimeInfo(
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
}
