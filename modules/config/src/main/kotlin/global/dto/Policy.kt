package io.github.junekim0007.cryptobench.config.global.dto

/**
 * The `policy` section. Applies at every stage — config, preparation, benchmark — to failures where the intent is
 * clear but the device cannot do it. A broken authored file always stops: its intent is unknown.
 */
data class Policy(
    val onFailure: OnFailure = OnFailure.SKIP,
) {

    /** STOP before anything runs, or SKIP the failed primitive, record why, and continue. */
    enum class OnFailure { STOP, SKIP }
}
