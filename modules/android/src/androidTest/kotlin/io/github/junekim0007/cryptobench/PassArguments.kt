package io.github.junekim0007.cryptobench

import androidx.test.platform.app.InstrumentationRegistry
import io.github.junekim0007.cryptobench.benchmark.run.CaseSettings
import io.github.junekim0007.cryptobench.benchmark.run.energy.Energy
import io.github.junekim0007.cryptobench.settings.Metric

/** The pass the host names (run.passes) and its samples, over a case's own settings; no pass argument keeps the settings as they are. */
object PassArguments {
    // Paired with scripts/session/passes.py PASS_ARGUMENT and SAMPLES_ARGUMENT.
    const val PASS = "cryptobench.pass"
    const val SAMPLES = "cryptobench.samples"
    private const val ENERGY = "energy"
    private const val ALLOCATION = "allocation"

    private val pass: String? get() = InstrumentationRegistry.getArguments().getString(PASS)

    val countsAllocations: Boolean get() = pass == ALLOCATION

    fun applied(settings: CaseSettings): CaseSettings {
        val named = pass ?: return settings
        val samples = InstrumentationRegistry.getArguments().getString(SAMPLES)?.toInt() ?: settings.iterations
        return settings.copy(
            iterations = samples,
            energy = if (named == ENERGY) settings.energy else settings.energy.copy(capture = Energy.Capture.NONE),
            metrics = when (named) {
                ENERGY -> setOf(Metric.TIME)
                ALLOCATION -> setOf(Metric.TIME, Metric.ALLOCATION)
                else -> settings.metrics
            },
        )
    }
}
