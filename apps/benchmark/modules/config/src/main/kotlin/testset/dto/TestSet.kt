package io.github.junekim0007.cryptobench.config.testset.dto

data class TestSet(
    val description: String,
    val include: List<Rule> = emptyList(),
    val exclude: List<Rule> = emptyList(),
    val overrides: List<Override> = emptyList(),
)
