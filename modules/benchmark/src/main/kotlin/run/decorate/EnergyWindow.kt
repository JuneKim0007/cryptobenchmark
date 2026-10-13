package io.github.junekim0007.cryptobench.benchmark.run.decorate

import io.github.junekim0007.cryptobench.benchmark.run.compose.CaseRun
import io.github.junekim0007.cryptobench.benchmark.run.energy.WindowMarker

// Dry pass only: Jetpack's trace session starts inside measureRepeated, after any marker
// opened around it, so a measured case's window is Jetpack's own timed phase.
class EnergyWindow(private val inner: CaseRun, private val marker: WindowMarker, private val caseId: String) : CaseRun {

    override fun run(): Long? {
        marker.begin(label(caseId))
        try {
            return inner.run()
        } finally {
            marker.end()
        }
    }

    companion object {
        // Paired with tools/energy/rails/trace.py MARKER_PREFIX; the two change together.
        const val PREFIX = "energy:"

        fun label(caseId: String): String = PREFIX + caseId
    }
}
