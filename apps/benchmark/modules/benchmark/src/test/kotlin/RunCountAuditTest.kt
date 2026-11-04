package io.github.junekim0007.cryptobench.benchmark

import io.github.junekim0007.cryptobench.benchmark.report.MetricSamples
import io.github.junekim0007.cryptobench.benchmark.report.jetpack.RunCountAudit
import org.junit.Assert.assertEquals
import org.junit.Test

class RunCountAuditTest {

    private fun runs(n: Int) = List(n) { 100.0 + it }

    private fun metrics(time: Int, allocations: Int? = null): Map<String, MetricSamples> = linkedMapOf<String, MetricSamples>(
        MetricSamples.TIME to MetricSamples(runs(time), 8192),
    ).apply { allocations?.let { put(MetricSamples.ALLOCATIONS, MetricSamples(runs(it), 1)) } }

    @Test
    fun runsThatMatchWhatWasAskedForAreSilent() {
        assertEquals(emptyList<String>(), RunCountAudit.findings("a", 50, metrics(50, 5)))
    }

    @Test
    fun aSettingThatNeverReachedTheTimerIsNamed() {
        assertEquals(listOf("iterations_not_applied: a asked for 5, timeNs has 50 runs"), RunCountAudit.findings("a", 5, metrics(50)))
    }

    @Test
    fun aCaseThatAskedForNothingIsNotHeldToAnything() {
        assertEquals(emptyList<String>(), RunCountAudit.findings("a", null, metrics(50)))
    }

    @Test
    fun allocationRunsAreHeldToWhatAndroidxUses() {
        assertEquals(emptyList<String>(), RunCountAudit.findings("a", 50, metrics(50, 5)))
        assertEquals(
            listOf("allocation_runs_changed: a has 50 allocationCount runs, androidx used 5 when this was written"),
            RunCountAudit.findings("a", null, metrics(50, 50)),
        )
    }
}
