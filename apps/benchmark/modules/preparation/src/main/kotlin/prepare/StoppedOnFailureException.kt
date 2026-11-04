package io.github.junekim0007.cryptobench.preparation.prepare

import io.github.junekim0007.cryptobench.preparation.report.Skip

class StoppedOnFailureException(val skipped: List<Skip>) :
    IllegalStateException("stopped_on_failure: ${skipped.size}\n" + skipped.joinToString("\n") { "  $it" })
