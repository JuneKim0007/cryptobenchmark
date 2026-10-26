package io.github.junekim0007.cryptobench.benchmark.run.compose

import io.github.junekim0007.cryptobench.benchmark.run.TimedLoop
import io.github.junekim0007.cryptobench.benchmark.run.decorate.Cooldown
import io.github.junekim0007.cryptobench.benchmark.run.decorate.EnergyWindow
import io.github.junekim0007.cryptobench.benchmark.run.decorate.Rewarm
import io.github.junekim0007.cryptobench.benchmark.run.energy.Energy
import io.github.junekim0007.cryptobench.benchmark.run.energy.WindowMarker
import io.github.junekim0007.cryptobench.preparation.operation.Invocation

object CaseRuns {

    fun timed(caseId: String, energy: Energy, timed: CaseRun): CaseRun = when (energy.capture) {
        Energy.Capture.NONE -> timed
        Energy.Capture.MEASURED -> Cooldown(timed, energy.cooldownMillis)
        Energy.Capture.DRY -> throw IllegalArgumentException("not_timed: $caseId is a dry energy case")
    }

    fun dry(caseId: String, energy: Energy, marker: WindowMarker, invocation: Invocation): CaseRun {
        require(energy.capture == Energy.Capture.DRY) { "not_dry: $caseId captures ${energy.capture}" }
        val window = EnergyWindow({ TimedLoop.run(invocation, energy.windowNanos) }, marker, caseId)
        return Cooldown(Rewarm(window, invocation, energy.warmupNanos), energy.cooldownMillis)
    }
}
