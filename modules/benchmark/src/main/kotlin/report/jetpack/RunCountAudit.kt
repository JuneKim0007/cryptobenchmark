package io.github.junekim0007.cryptobench.benchmark.report.jetpack

import io.github.junekim0007.cryptobench.benchmark.report.MetricSamples

object RunCountAudit {

    // androidx hard-codes the allocation phase at five runs, whatever `iterations` says.
    const val ALLOCATION_RUNS = 5

    fun findings(id: String, requestedIterations: Int?, metrics: Map<String, MetricSamples>): List<String> {
        val findings = mutableListOf<String>()
        val time = metrics[MetricSamples.TIME]
        if (requestedIterations != null && time != null && time.runs.size != requestedIterations) {
            findings += "iterations_not_applied: $id asked for $requestedIterations, ${MetricSamples.TIME} has ${time.runs.size} runs"
        }
        val allocations = metrics[MetricSamples.ALLOCATIONS]
        if (allocations != null && allocations.runs.size != ALLOCATION_RUNS) {
            findings += "allocation_runs_changed: $id has ${allocations.runs.size} ${MetricSamples.ALLOCATIONS} runs, androidx used $ALLOCATION_RUNS when this was written"
        }
        return findings
    }
}
