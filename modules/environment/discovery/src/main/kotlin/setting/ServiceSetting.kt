package io.github.junekim0007.cryptobench.discovery.setting

data class ServiceSetting(
    val type: String,
    val algorithm: String,
    val aliases: List<String> = emptyList(),
    val supportedModes: List<String> = emptyList(),
    val supportedPaddings: List<String> = emptyList(),
    val keySize: Int? = null,
)
