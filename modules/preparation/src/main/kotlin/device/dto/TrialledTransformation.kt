package io.github.junekim0007.cryptobench.preparation.device.dto

data class TrialledTransformation(
    val name: String,
    val instantiates: Boolean,
    val error: String = "",
)
