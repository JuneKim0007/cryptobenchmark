package io.github.junekim0007.cryptobench.preparation.prepare

import io.github.junekim0007.cryptobench.preparation.report.Skip

/** onFailure = STOP and preparation found failures: every one is listed, and skipped.yaml is written before this is thrown. */
class StoppedOnFailureException(val skipped: List<Skip>) :
    IllegalStateException("stopped_on_failure: ${skipped.size}\n" + skipped.joinToString("\n") { "  $it" })
