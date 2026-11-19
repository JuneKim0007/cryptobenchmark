package io.github.junekim0007.cryptobench.config.global.dto

import io.github.junekim0007.cryptobench.settings.OnFailure

data class Policy(
    val onFailure: OnFailure = OnFailure.SKIP,
)
