package io.github.junekim0007.cryptobench.config.generate

import io.github.junekim0007.cryptobench.config.contract.RunSettings

object RunDefaults {

    fun standard(): RunSettings = RunSettings(
        inputSizes = listOf(1024),
        phases = listOf("WARM"),
        metrics = listOf("TIME"),
        processRepetitions = 1,
        seed = 0L,
    )
}
