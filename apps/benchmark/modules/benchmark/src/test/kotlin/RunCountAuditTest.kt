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
    fun allocationRunsAsAndroidxUsesThemAreSilent() {
        assertEquals(emptyList<String>(), RunCountAudit.findings("a", metrics(50, 5)))
    }

    @Test
    fun allocationRunsAreHeldToWhatAndroidxUses() {
        assertEquals(
            listOf("allocation_runs_changed: a has 50 allocationCount runs, androidx used 5 when this was written"),
            RunCountAudit.findings("a", metrics(50, 50)),
        )
    }
}
