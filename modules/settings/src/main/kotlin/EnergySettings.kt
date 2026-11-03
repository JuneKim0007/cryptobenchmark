package io.github.junekim0007.cryptobench.settings

data class EnergySettings(
    val capture: String? = null,
    val windowSeconds: Int? = null,
    val warmupSeconds: Int? = null,
    val cooldownSeconds: Int? = null,
    val source: String? = null,
) {
    init {
        require(capture == null || capture in CAPTURES) { "invalid: energy.capture $capture, known $CAPTURES" }
        require(windowSeconds == null || windowSeconds >= 1) { "not_positive: energy.windowSeconds $windowSeconds" }
        require(warmupSeconds == null || warmupSeconds >= 1) { "not_positive: energy.warmupSeconds $warmupSeconds" }
        require(cooldownSeconds == null || cooldownSeconds >= 0) { "negative: energy.cooldownSeconds $cooldownSeconds" }
        require(source == null || source in SOURCES) { "invalid: energy.source $source, known $SOURCES" }
    }

    val isEmpty: Boolean get() = this == EnergySettings()

    val needsRails: Boolean get() = source == null || source == RAILS

    fun mergedWith(later: EnergySettings?): EnergySettings = ENERGY.merged(this, later)

    companion object {
        val CAPTURES: List<String> = listOf("none", "measured", "dry")

        const val RAILS = "rails"

        val SOURCES: List<String> = listOf(RAILS, "manafa")

        val ENERGY: Section<EnergySettings> = Section(EnergySettings(), "energy.") {
            listOf(
                Leaf("capture", Values.text(CAPTURES), { it.capture }, { o, v -> o.copy(capture = v) }),
                Leaf("windowSeconds", Values.int, { it.windowSeconds }, { o, v -> o.copy(windowSeconds = v) }),
                Leaf("warmupSeconds", Values.int, { it.warmupSeconds }, { o, v -> o.copy(warmupSeconds = v) }),
                Leaf("cooldownSeconds", Values.int, { it.cooldownSeconds }, { o, v -> o.copy(cooldownSeconds = v) }),
                Leaf("source", Values.text(SOURCES), { it.source }, { o, v -> o.copy(source = v) }),
            )
        }
    }
}
