package io.github.junekim0007.cryptobench.preparation.device.dto

data class TrialledDevice(
    val capturedAtMillis: Long,
    val services: List<TrialledService> = emptyList(),
)
