package io.github.junekim0007.cryptobench.preparation.device.dto

data class CapturedDevice(
    val capturedAtMillis: Long,
    val providers: List<CapturedProvider> = emptyList(),
)
