package io.github.junekim0007.cryptobench.discovery.contract

data class RuntimeInfo(
    val model: String = "",
    val manufacturer: String = "",
    val hardware: String = "",
    val sdkInt: Int = 0,
    val release: String = "",
    val javaVersion: String = "",
    val defaultKeySizeProperty: String = "",
)
