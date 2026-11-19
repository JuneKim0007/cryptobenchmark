package io.github.junekim0007.cryptobench.config.global.dto

import io.github.junekim0007.cryptobench.settings.Leaf
import io.github.junekim0007.cryptobench.settings.Section
import io.github.junekim0007.cryptobench.settings.Values

/** One device pass of run.passes: its metric group, the timed samples each case takes in it, and for energy the shortest window a case keeps. */
data class MeasurePass(val name: String, val samples: Int? = null, val minWindowSeconds: Int? = if (name == ENERGY) MIN_WINDOW_SECONDS else null) {

    /** The entry PASS read, named and checked under path. */
    fun resolved(path: String): MeasurePass {
        require(name in NAMES) { "invalid: $path, known $NAMES" }
        val samples = samples ?: throw IllegalArgumentException("missing_field: $path.samples")
        require(samples >= 1) { "not_positive: $path.samples $samples" }
        require(minWindowSeconds == null || name == ENERGY) { "not_supported: $path.minWindowSeconds; only the energy pass sizes its window" }
        require(minWindowSeconds == null || minWindowSeconds >= 1) { "not_positive: $path.minWindowSeconds $minWindowSeconds" }
        return this
    }

    companion object {
        const val TIMING = "timing"
        const val ENERGY = "energy"
        const val ALLOCATION = "allocation"

        // power-rail polling: 20 polls of 250 ms read a valid window
        const val MIN_WINDOW_SECONDS = 5

        // Paired with lib/cryptobench/cryptobench/stages/measurement/session/passes.py TIMING, ENERGY, ALLOCATION.
        val NAMES: List<String> = listOf(TIMING, ENERGY, ALLOCATION)

        /** The keys of one pass entry; read(name) starts from the pass's own defaults. */
        fun table(name: String): Section<MeasurePass> = Section(MeasurePass(name), "") {
            listOf(
                Leaf("samples", Values.int, { it.samples }, { o, v -> o.copy(samples = v) }),
                Leaf("minWindowSeconds", Values.int, { it.minWindowSeconds }, { o, v -> o.copy(minWindowSeconds = v) }),
            )
        }
    }
}
