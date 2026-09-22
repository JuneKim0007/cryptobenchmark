package io.github.junekim0007.cryptobench.discovery.adapter

import io.github.junekim0007.cryptobench.discovery.contract.RuntimeInfo

object DeviceRuntimeReader {

    const val DEFAULT_KEY_SIZE_PROPERTY = "jdk.security.defaultKeySize"

    fun read(): RuntimeInfo = RuntimeInfo(
        model = buildField("android.os.Build", "MODEL"),
        manufacturer = buildField("android.os.Build", "MANUFACTURER"),
        hardware = buildField("android.os.Build", "HARDWARE"),
        sdkInt = sdkInt(),
        release = buildField("android.os.Build\$VERSION", "RELEASE"),
        javaVersion = System.getProperty("java.version") ?: "",
        defaultKeySizeProperty = System.getProperty(DEFAULT_KEY_SIZE_PROPERTY) ?: "",
    )

    private fun buildField(className: String, name: String): String = try {
        Class.forName(className).getField(name).get(null).toString()
    } catch (e: Exception) {
        ""
    }

    private fun sdkInt(): Int = try {
        Class.forName("android.os.Build\$VERSION").getField("SDK_INT").get(null) as? Int ?: 0
    } catch (e: Exception) {
        0
    }
}
