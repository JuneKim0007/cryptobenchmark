package io.github.junekim0007.cryptobench.discovery.contract

data class RuntimeInfo(
    val model: String = "",
    val manufacturer: String = "",
    val hardware: String = "",
    val sdkInt: Int = 0,
    val release: String = "",
    val javaVersion: String = System.getProperty("java.version") ?: "",
    val defaultKeySizeProperty: String = System.getProperty(DEFAULT_KEY_SIZE_PROPERTY) ?: "",
) {

    companion object {
        const val DEFAULT_KEY_SIZE_PROPERTY = "jdk.security.defaultKeySize"

        fun unknown(): RuntimeInfo = RuntimeInfo()
    }
}
