package io.github.junekim0007.cryptobench

import io.github.junekim0007.cryptobench.benchmark.run.CaseSettings
import io.github.junekim0007.cryptobench.benchmark.run.compose.CaseRuns

/** One timed case under its cpu and energy settings: pin, record the pin, run, restore. */
internal object PinnedCase {

    fun run(caseId: String, settings: CaseSettings, timed: () -> Unit) {
        val cpu = settings.cpu
        (cpu?.let(CorePin::apply)).use { pin ->
            if (cpu != null && pin != null) CorePins.record(caseId, cpu, pin.outcome)
            val failed = pin?.outcome as? CorePin.Outcome.Failed
            check(failed == null || cpu?.isRequired != true) { "cpu_pin_failed: ${failed?.reason}" }
            CaseRuns.timed(caseId, settings.energy) {
                timed()
                null
            }.run()
        }
    }
}
