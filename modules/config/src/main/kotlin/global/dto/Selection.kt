package io.github.junekim0007.cryptobench.config.global.dto

import io.github.junekim0007.cryptobench.config.testset.dto.Rule

data class Selection(
    val testSet: String,
    val exclude: List<Rule> = emptyList(),
) {

    init {
        require(testSet.isNotBlank()) { "missing_field: testSet" }
    }
}
