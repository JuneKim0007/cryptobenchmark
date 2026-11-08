package io.github.junekim0007.cryptobench.preparation.prepare

import io.github.junekim0007.cryptobench.preparation.global.GlobalSettings
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.report.Skip

/** The cases an effective file expands to on this device, before any key is made or provider called; skipped holds the rejected selections. */
class Listing(
    val cases: List<BenchmarkCase>,
    val skipped: List<Skip>,
    val global: GlobalSettings,
    val effectiveFileName: String,
    val runId: String?,
)
