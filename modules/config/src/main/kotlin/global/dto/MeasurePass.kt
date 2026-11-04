package io.github.junekim0007.cryptobench.config.global.dto

/** One device pass of run.passes: its metric group and the timed samples each case takes in it. */
data class MeasurePass(val name: String, val samples: Int) {

    init {
        require(name in NAMES) { "invalid: run.passes.$name, known $NAMES" }
        require(samples >= 1) { "not_positive: run.passes.$name.samples $samples" }
    }

    companion object {
        const val TIMING = "timing"
        const val ENERGY = "energy"
        const val ALLOCATION = "allocation"

        // Paired with scripts/session/passes.py NAMES.
        val NAMES: List<String> = listOf(TIMING, ENERGY, ALLOCATION)
    }
}
