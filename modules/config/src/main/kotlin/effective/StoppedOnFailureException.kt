package io.github.junekim0007.cryptobench.config.effective

import io.github.junekim0007.cryptobench.config.effective.dto.Skip

class StoppedOnFailureException(val skipped: List<Skip>) :
    IllegalStateException("stopped_on_failure: ${skipped.size}\n" + skipped.joinToString("\n") { "  $it" })
