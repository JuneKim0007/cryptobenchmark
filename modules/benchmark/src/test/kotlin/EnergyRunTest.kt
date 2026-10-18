package io.github.junekim0007.cryptobench.benchmark

import io.github.junekim0007.cryptobench.benchmark.run.compose.CaseRun
import io.github.junekim0007.cryptobench.benchmark.run.compose.CaseRuns
import io.github.junekim0007.cryptobench.benchmark.run.decorate.Cooldown
import io.github.junekim0007.cryptobench.benchmark.run.energy.Energy
import io.github.junekim0007.cryptobench.benchmark.run.decorate.EnergyWindow
import io.github.junekim0007.cryptobench.benchmark.run.TimedLoop
import io.github.junekim0007.cryptobench.benchmark.run.energy.WindowMarker
import io.github.junekim0007.cryptobench.settings.EnergySettings
import io.github.junekim0007.cryptobench.preparation.operation.Invocation
import org.junit.Assert.assertEquals
import org.junit.Assert.assertSame
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test

class EnergyRunTest {

    private class Recorder(private val calls: () -> Int = { 0 }) : WindowMarker {
        val events = mutableListOf<String>()
        override fun begin(label: String) { events += "begin $label at ${calls()}" }
        override fun end() { events += "end at ${calls()}" }
    }

    private val timed = CaseRun { null }

    @Test
    fun withoutEnergyTheTimedRunIsUntouched() {
        assertSame(timed, CaseRuns.timed("c", Energy.NONE, timed))
    }

    @Test
    fun aMeasuredRunIsCooledDownAfterJetpack() {
        val events = mutableListOf<String>()
        val run = Cooldown(CaseRun { events += "jetpack"; null }, 3000) { events += "sleep $it" }
        run.run()
        assertEquals(listOf("jetpack", "sleep 3000"), events)
        assertTrue(CaseRuns.timed("m", Energy.of(EnergySettings(capture = "measured")), timed) is Cooldown)
    }

    @Test
    fun theMarkerClosesEvenWhenTheRunFails() {
        val marker = Recorder()
        assertThrows(IllegalStateException::class.java) { EnergyWindow(CaseRun { error("boom") }, marker, "c").run() }
        assertEquals(listOf("begin energy:c at 0", "end at 0"), marker.events)
    }

    @Test
    fun aDryRunWarmsBeforeItsWindowAndCountsOnlyInside() {
        var calls = 0
        val marker = Recorder { calls }
        val energy = Energy(Energy.Capture.DRY, windowSeconds = 1, warmupSeconds = 1, cooldownSeconds = 0)
        val counted = CaseRuns.dry("d", energy, marker, Invocation({ calls++ })).run()!!
        val begunAt = marker.events[0].substringAfter(" at ").toInt()
        val endedAt = marker.events[1].substringAfter(" at ").toInt()
        assertTrue("warm-up ran before the window opened", begunAt > 0)
        assertEquals(counted, (endedAt - begunAt).toLong())
        assertEquals(calls, endedAt)
    }

    @Test
    fun aDryCaseIsNeverTimedAndATimedOneNeverDry() {
        val dry = Energy(Energy.Capture.DRY, 1, 1, 0)
        assertThrows(IllegalArgumentException::class.java) { CaseRuns.timed("d", dry, timed) }
        assertThrows(IllegalArgumentException::class.java) { CaseRuns.dry("m", Energy.NONE, Recorder(), Invocation({ null })) }
    }

    @Test
    fun theLoopReadsTheClockOncePerCall() {
        var now = 0L
        assertEquals(3L, TimedLoop.run(Invocation({ null }), 10, clock = { now.also { now += 3 } }))
    }
}
