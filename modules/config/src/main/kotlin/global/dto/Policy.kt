package io.github.junekim0007.cryptobench.config.global.dto

/** The `policy` section. */
data class Policy(
    val onUnavailable: OnUnavailable = OnUnavailable.SKIP,
) {

    /** A selected primitive this device cannot run: skip it and record why, or stop before anything runs. */
    enum class OnUnavailable { SKIP, FAIL }
}
