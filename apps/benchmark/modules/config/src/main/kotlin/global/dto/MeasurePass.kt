package io.github.junekim0007.cryptobench.config.global.dto

/** One device pass of run.passes: its metric group, the timed samples each case takes in it, and for energy the shortest window a case keeps. */
data class MeasurePass(val name: String, val samples: Int, val minWindowSeconds: Int? = if (name == ENERGY) MIN_WINDOW_SECONDS else null) {

    init {
        require(name in NAMES) { "invalid: run.passes.$name, known $NAMES" }
        require(samples >= 1) { "not_positive: run.passes.$name.samples $samples" }
        require(minWindowSeconds == null || name == ENERGY) { "not_supported: run.passes.$name.minWindowSeconds; only the energy pass sizes its window" }
        require(minWindowSeconds == null || minWindowSeconds >= 1) { "not_positive: run.passes.$name.minWindowSeconds $minWindowSeconds" }
    }

    companion object {
        const val TIMING = "timing"
        const val ENERGY = "energy"
        const val ALLOCATION = "allocation"

        // power-rail polling: 20 polls of 250 ms read a valid window
        const val MIN_WINDOW_SECONDS = 5

        // Paired with lib/cryptobench/cryptobench/stages/measurement/session/passes.py TIMING, ENERGY, ALLOCATION.
        val NAMES: List<String> = listOf(TIMING, ENERGY, ALLOCATION)
    }
}
