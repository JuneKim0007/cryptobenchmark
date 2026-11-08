package io.github.junekim0007.cryptobench.benchmark

import io.github.junekim0007.cryptobench.benchmark.budget.NativeBudget
import io.github.junekim0007.cryptobench.benchmark.budget.NativeCleanup
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test

class NativeBudgetTest {

    @Test
    fun theBudgetFallsDueOnceEveryKCalls() {
        val budget = NativeBudget(calls = 3)
        assertEquals(listOf(false, false, true, false, false, true, false), (1..7).map { budget.due() })
    }

    @Test
    fun eachCleanupIsCountedAndItsPauseSummed() {
        val budget = NativeBudget(calls = 1)
        val paused = (1..2).sumOf { budget.clean() }
        val spent = budget.spent
        assertEquals(NativeCleanup(1, 2, paused), spent)
        assertTrue(spent.pausedNanos > 0)
    }

    @Test
    fun theReportedFieldReadsBackAndMergedProcessesAddUp() {
        val one = NativeCleanup(50_000, 2, 1_000)
        assertEquals(one, NativeCleanup.read(one.toMap()))
        assertEquals(NativeCleanup(50_000, 5, 4_000), one.mergedWith(NativeCleanup(50_000, 3, 3_000)))
        assertNull(NativeCleanup.read(null))
        val missing = assertThrows(IllegalArgumentException::class.java) { NativeCleanup.read(mapOf("everyCalls" to 1)) }
        assertEquals("missing_field: nativeCleanup.cleanups", missing.message)
    }
}
