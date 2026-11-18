package io.github.junekim0007.cryptobench.config.global.dto

data class GlobalConfig(
    val selection: Selection,
    val run: RunSettings,
    val policy: Policy = Policy(),
    val analysis: AnalysisSettings = AnalysisSettings(),
    val providers: ProviderSources = ProviderSources(),
    // what the parse fell back from, for report.yaml
    val notices: List<String> = emptyList(),
)
