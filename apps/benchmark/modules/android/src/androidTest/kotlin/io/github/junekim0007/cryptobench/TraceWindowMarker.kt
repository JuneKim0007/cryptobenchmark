package io.github.junekim0007.cryptobench

import android.os.Trace
import io.github.junekim0007.cryptobench.benchmark.run.energy.WindowMarker

// Captured only because tools/energy/energy.pbtx lists this app in atrace_apps.
object TraceWindowMarker : WindowMarker {

    // atrace truncates longer section names, which would make two windows indistinguishable.
    private const val MAX_LABEL = 127

    override fun begin(label: String) {
        require(label.length <= MAX_LABEL) { "too_long: trace section $label (${label.length} > $MAX_LABEL)" }
        Trace.beginSection(label)
    }

    override fun end() = Trace.endSection()
}
