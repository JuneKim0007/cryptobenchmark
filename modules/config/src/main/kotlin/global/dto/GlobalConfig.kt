package io.github.junekim0007.cryptobench.config.global.dto

data class GlobalConfig(
    val selection: Selection,
    val run: RunSettings = RunSettings(),
    val policy: Policy = Policy(),
)
