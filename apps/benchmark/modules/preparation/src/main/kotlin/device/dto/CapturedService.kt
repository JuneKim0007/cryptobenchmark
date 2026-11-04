package io.github.junekim0007.cryptobench.preparation.device.dto

data class CapturedService(
    val type: String,
    val algorithm: String,
    val aliases: List<String> = emptyList(),
)
