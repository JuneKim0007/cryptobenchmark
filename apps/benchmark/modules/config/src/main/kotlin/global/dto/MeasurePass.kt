package io.github.junekim0007.cryptobench.config.global.dto

import io.github.junekim0007.cryptobench.settings.Leaf
import io.github.junekim0007.cryptobench.settings.Nested
import io.github.junekim0007.cryptobench.settings.Section
import io.github.junekim0007.cryptobench.settings.Values

/** One device pass of run.passes: its samples, energy's shortest window, and its own thermalGate and caseCooldownSeconds, set only when written. */
data class MeasurePass(
    val name: String,
    val samples: Int? = null,
    val minWindowSeconds: Int? = if (name == ENERGY) MIN_WINDOW_SECONDS else null,
    val thermalGate: ThermalGate? = null,
    val caseCooldownSeconds: Int? = null,
) {

    /** The entry the table read, checked under path, its gate resolved over runGate (or the defaults when the run has none). */
    fun resolved(path: String, runGate: ThermalGate?): MeasurePass {
        require(name in NAMES) { "invalid: $path, known $NAMES" }
        val samples = samples ?: throw IllegalArgumentException("missing_field: $path.samples")
        require(samples >= 1) { "not_positive: $path.samples $samples" }
        require(minWindowSeconds == null || name == ENERGY) { "not_supported: $path.minWindowSeconds; only the energy pass sizes its window" }
        require(minWindowSeconds == null || minWindowSeconds >= 1) { "not_positive: $path.minWindowSeconds $minWindowSeconds" }
        require(caseCooldownSeconds == null || caseCooldownSeconds >= 0) { "negative: $path.caseCooldownSeconds $caseCooldownSeconds" }
        return copy(thermalGate = thermalGate?.resolved(runGate ?: ThermalGate.DEFAULTS, "$path.thermalGate"))
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
                Nested("thermalGate", ThermalGate.GATE, { it.thermalGate }, { o, v -> o.copy(thermalGate = v) }),
                Leaf("caseCooldownSeconds", Values.int, { it.caseCooldownSeconds }, { o, v -> o.copy(caseCooldownSeconds = v) }),
            )
        }
    }
}
