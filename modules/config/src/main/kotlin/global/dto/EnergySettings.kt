package io.github.junekim0007.cryptobench.config.global.dto

data class EnergySettings(
    val capture: String? = null,
    val windowSeconds: Int? = null,
    val warmupSeconds: Int? = null,
    val cooldownSeconds: Int? = null,
) {

    init {
        require(capture == null || capture in CAPTURES) { "invalid: energy.capture $capture, known $CAPTURES" }
        require(windowSeconds == null || windowSeconds >= 1) { "not_positive: energy.windowSeconds $windowSeconds" }
        require(warmupSeconds == null || warmupSeconds >= 1) { "not_positive: energy.warmupSeconds $warmupSeconds" }
        require(cooldownSeconds == null || cooldownSeconds >= 0) { "negative: energy.cooldownSeconds $cooldownSeconds" }
    }

    val isEmpty: Boolean get() = capture == null && windowSeconds == null && warmupSeconds == null && cooldownSeconds == null

    fun mergedWith(later: EnergySettings?): EnergySettings =
        if (later == null) this else EnergySettings(
            capture = later.capture ?: capture,
            windowSeconds = later.windowSeconds ?: windowSeconds,
            warmupSeconds = later.warmupSeconds ?: warmupSeconds,
            cooldownSeconds = later.cooldownSeconds ?: cooldownSeconds,
        )

    companion object {
        val CAPTURES: List<String> = listOf("none", "measured", "dry")
    }
}
