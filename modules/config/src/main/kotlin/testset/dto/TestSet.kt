package io.github.junekim0007.cryptobench.config.testset.dto

/**
 * A named set of primitives, independent of any device: rules, not provider lists.
 * An empty include means everything the inventory can run.
 */
data class TestSet(
    val description: String,
    val include: List<Rule> = emptyList(),
    val exclude: List<Rule> = emptyList(),
    val overrides: List<Override> = emptyList(),
)
