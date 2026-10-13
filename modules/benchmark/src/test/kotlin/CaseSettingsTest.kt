package io.github.junekim0007.cryptobench.benchmark

import io.github.junekim0007.cryptobench.benchmark.run.CaseSettings
import io.github.junekim0007.cryptobench.benchmark.run.CaseSettings.Profiling
import io.github.junekim0007.cryptobench.preparation.global.HarnessSettings
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

class CaseSettingsTest {

    @Test
    fun aHarnessWithNothingSetAsksForNothing() {
        assertEquals(CaseSettings(null, null, Profiling.NONE), CaseSettings.of(HarnessSettings()))
    }

    @Test
    fun theHarnessWordsBecomeSettings() {
        assertEquals(CaseSettings(50, 20, Profiling.METHOD_TRACING), CaseSettings.of(HarnessSettings(50, 20, "MethodTracing")))
        assertEquals(Profiling.STACK_SAMPLING, CaseSettings.of(HarnessSettings(profiling = "StackSampling")).profiling)
        assertEquals(Profiling.NONE, CaseSettings.of(HarnessSettings(profiling = "none")).profiling)
    }

    @Test
    fun aWarmupOfZeroIsNotSupported() {
        val refused = assertThrows(IllegalArgumentException::class.java) { CaseSettings.of(HarnessSettings(warmupIterations = 0)) }
        assertEquals("not_supported: warmupIterations 0, androidx needs at least 1; leave it out to let the library decide", refused.message)
    }
}
