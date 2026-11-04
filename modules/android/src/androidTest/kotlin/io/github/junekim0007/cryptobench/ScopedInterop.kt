package io.github.junekim0007.cryptobench

import org.junit.Test

// Run alone, before ScopedBenchmark: one process checks every scope and prepares every call site, so no measured process reruns either.
class ScopedInterop {

    @Test
    fun checksEveryScope() {
        ScopeInteropFile.write(DevicePlan.directory, ScopedPlan.scopes.map(ScopeCheck::of))
        CallSitePlan.writeVerdicts()
    }
}
