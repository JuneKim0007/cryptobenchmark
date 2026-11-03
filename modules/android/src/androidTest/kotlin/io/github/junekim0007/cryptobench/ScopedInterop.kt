package io.github.junekim0007.cryptobench

import org.junit.Test

// Run alone, before ScopedBenchmark: one process checks every scope, so a process per measured case never reruns the check.
class ScopedInterop {

    @Test
    fun checksEveryScope() {
        ScopeInteropFile.write(DevicePlan.directory, ScopedPlan.scopes.map(ScopeCheck::of))
    }
}
