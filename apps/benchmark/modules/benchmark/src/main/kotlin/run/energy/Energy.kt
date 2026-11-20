package io.github.junekim0007.cryptobench.benchmark.run.energy

import io.github.junekim0007.cryptobench.settings.EnergySettings

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

        /** settings over EnergySettings.DEFAULTS key by key. */
        fun of(settings: EnergySettings): Energy = EnergySettings.DEFAULTS.mergedWith(settings).let {
            Energy(Capture.of(it.capture), it.windowSeconds!!, it.warmupSeconds!!, it.cooldownSeconds!!)
        }

        val NONE = of(EnergySettings())
    }
}
