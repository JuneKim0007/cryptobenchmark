package io.github.junekim0007.cryptobench.config.global.dto

data class Policy(
    val onFailure: OnFailure = OnFailure.SKIP,
) {

    enum class OnFailure { STOP, SKIP }
}
