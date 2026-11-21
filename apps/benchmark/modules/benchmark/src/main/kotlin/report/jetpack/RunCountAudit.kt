package io.github.junekim0007.cryptobench.benchmark.report.jetpack

import io.github.junekim0007.cryptobench.benchmark.report.MetricSamples

object RunCountAudit {

    // androidx hard-codes the allocation phase at five runs, whatever `iterations` says.
    const val ALLOCATION_RUNS = 5

    fun findings(id: String, metrics: Map<String, MetricSamples>, sampledAllocations: Boolean = false): List<String> {
        val findings = mutableListOf<String>()
        val allocations = metrics[MetricSamples.ALLOCATIONS]
        if (allocations != null && !sampledAllocations && allocations.runs.size != ALLOCATION_RUNS) {
            findings += "allocation_runs_changed: $id has ${allocations.runs.size} ${MetricSamples.ALLOCATIONS} runs, androidx used $ALLOCATION_RUNS when this was written"
        }
        return findings
    }
}
