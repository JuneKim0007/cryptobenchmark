package io.github.junekim0007.cryptobench.config.global.dto

import io.github.junekim0007.cryptobench.config.testset.dto.Rule

/** The `selection` section: which test set, and what to drop from it on top. */
data class Selection(
    /** Relative to the directory of global.yaml. */
    val testSet: String,
    val exclude: List<Rule> = emptyList(),
) {

    init {
        require(testSet.isNotBlank()) { "missing_field: testSet" }
    }
}
