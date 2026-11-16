package io.github.junekim0007.cryptobench.config.testset.dto

data class TestSet(
    val description: String,
    val include: List<Include> = emptyList(),
    val exclude: List<Rule> = emptyList(),
    val overrides: List<Override> = emptyList(),
    // what the parse fell back from, for report.yaml
    val notices: List<String> = emptyList(),
)
