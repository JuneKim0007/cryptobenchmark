package io.github.junekim0007.cryptobench.preparation.device.dto

data class TrialledService(
    val provider: String,
    val type: String,
    val algorithm: String,
    val instantiates: Boolean,
    val error: String = "",
    val transformations: List<TrialledTransformation> = emptyList(),
)
