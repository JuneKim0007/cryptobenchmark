package io.github.junekim0007.cryptobench.preparation.request

import io.github.junekim0007.cryptobench.preparation.global.GlobalSettings

data class BenchmarkRequest(
    val selections: List<Selection>,
    val global: GlobalSettings = GlobalSettings(),
) {

    init {
        require(selections.isNotEmpty()) { "missing_field: selections" }
        require(selections.size == selections.distinct().size) { "duplicate: selections" }
    }
}
