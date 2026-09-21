package io.github.junekim0007.cryptobench.preparation.resolve

import io.github.junekim0007.cryptobench.preparation.request.Selection

/** One thing asked for that will not run on this device, and why. */
data class Rejection(
    val selection: Selection,
    val provider: String?,
    val reason: String,
) {

    override fun toString(): String = "${selection.type}/${selection.algorithm}@${provider ?: "*"}: $reason"
}
