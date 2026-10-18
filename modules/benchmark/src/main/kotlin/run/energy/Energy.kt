package io.github.junekim0007.cryptobench.benchmark.run.energy

import io.github.junekim0007.cryptobench.settings.EnergySettings

// A window under ~20 rail polls (250 ms each in Jetpack's trace) loses a few percent to edge interpolation.
data class Energy(val capture: Capture, val windowSeconds: Int, val warmupSeconds: Int, val cooldownSeconds: Int) {

    enum class Capture { NONE, MEASURED, DRY }

    val windowNanos: Long get() = windowSeconds * NANOS
    val warmupNanos: Long get() = warmupSeconds * NANOS
    val cooldownMillis: Long get() = cooldownSeconds * 1_000L

    companion object {
        private const val NANOS = 1_000_000_000L
        const val WINDOW_SECONDS = 10
        const val WARMUP_SECONDS = 2
        const val COOLDOWN_SECONDS = 5

        val NONE = Energy(Capture.NONE, WINDOW_SECONDS, WARMUP_SECONDS, COOLDOWN_SECONDS)

        fun of(settings: EnergySettings): Energy = Energy(
            capture = when (settings.capture) {
                null, "none" -> Capture.NONE
                "measured" -> Capture.MEASURED
                "dry" -> Capture.DRY
                else -> throw IllegalArgumentException("invalid: energy.capture ${settings.capture}")
            },
            windowSeconds = settings.windowSeconds ?: WINDOW_SECONDS,
            warmupSeconds = settings.warmupSeconds ?: WARMUP_SECONDS,
            cooldownSeconds = settings.cooldownSeconds ?: COOLDOWN_SECONDS,
        )
    }
}
