package io.github.junekim0007.cryptobench.config.global.dto

/**
 * global.yaml: one section per feature, each read only by the feature that owns it.
 * A later feature adds a section here; the existing ones do not change.
 */
data class GlobalConfig(
    val selection: Selection,
    val run: RunSettings = RunSettings(),
    val policy: Policy = Policy(),
)
