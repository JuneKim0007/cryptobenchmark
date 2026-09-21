package io.github.junekim0007.cryptobench.config.effective

import io.github.junekim0007.cryptobench.config.effective.dto.Skip

/** policy.onUnavailable = FAIL and something selected cannot run: every skip is listed, not just the first. */
class UnavailableSelectionException(val skipped: List<Skip>) :
    IllegalStateException("unavailable_selection: ${skipped.size}\n" + skipped.joinToString("\n") { "  $it" })
