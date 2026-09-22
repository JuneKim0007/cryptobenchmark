package io.github.junekim0007.cryptobench.preparation.device.dto

data class CapturedProvider(
    val name: String,
    val precedence: Int,
    val services: List<CapturedService> = emptyList(),
)
