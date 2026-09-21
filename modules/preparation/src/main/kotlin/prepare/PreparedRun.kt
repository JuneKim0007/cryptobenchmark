package io.github.junekim0007.cryptobench.preparation.prepare

import io.github.junekim0007.cryptobench.preparation.report.Skip

data class PreparedRun(
    val cases: List<PreparedCase>,
    val skipped: List<Skip>,
    val processRepetitions: Int,
)
