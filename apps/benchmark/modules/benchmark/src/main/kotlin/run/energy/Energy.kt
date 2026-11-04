package io.github.junekim0007.cryptobench.benchmark.run.energy

import io.github.junekim0007.cryptobench.settings.EnergySettings

// A window under ~20 rail polls (250 ms each in Jetpack's trace) loses a few percent to edge interpolation.
data class Energy(val capture: Capture, val windowSeconds: Int, val warmupSeconds: Int, val cooldownSeconds: Int) {

    enum class Capture {
        NONE, MEASURED, DRY;

        companion object {
            private val BY_SETTING: Map<String, Capture> = EnergySettings.CAPTURES.associateWith { valueOf(it.uppercase()) }

            fun of(capture: String?): Capture =
                if (capture == null) NONE else BY_SETTING[capture] ?: throw IllegalArgumentException("invalid: energy.capture $capture")
        }
    }

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
            capture = Capture.of(settings.capture),
            windowSeconds = settings.windowSeconds ?: WINDOW_SECONDS,
            warmupSeconds = settings.warmupSeconds ?: WARMUP_SECONDS,
            cooldownSeconds = settings.cooldownSeconds ?: COOLDOWN_SECONDS,
        )
    }
}
