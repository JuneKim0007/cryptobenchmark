package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.operation.EngineCall
import io.github.junekim0007.cryptobench.preparation.operation.PerCall
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.lang.management.ManagementFactory

class EngineCallTest {

    private class Counted {
        var made = 0
        var inits = 0
        var operations = 0
    }

    private fun counted(perCall: PerCall, calls: Int): Counted {
        val counts = Counted()
        val invocation = EngineCall({ counts.made++; Any() }, { _, _ -> counts.inits++ }, { counts.operations++ }).invocation(perCall)
        repeat(calls) { invocation.perIteration() }
        assertEquals(perCall, invocation.perCall)
        return counts
    }

    @Test
    fun setupBeforeTheTimedCallRunsOnceAndThePerCallPartEveryCall() {
        fun triple(counts: Counted) = Triple(counts.made, counts.inits, counts.operations)
        assertEquals(Triple(1, 1, 5), triple(counted(PerCall.OPERATION, 5)))
        assertEquals(Triple(1, 6, 5), triple(counted(PerCall.INIT_AND_OPERATION, 5)))
        assertEquals(Triple(6, 6, 5), triple(counted(PerCall.INSTANCE_INIT_AND_OPERATION, 5)))
    }

    @Test
    fun theTraceReadsTheHeldEngineAndTheInitCount() {
        fun traced(perCall: PerCall): Pair<Boolean, Int> {
            val invocation = EngineCall({ Any() }, { _, _ -> }, { null }).invocation(perCall)
            val before = invocation.trace!!
            repeat(3) { invocation.perIteration() }
            val after = invocation.trace!!
            return (after.engine !== before.engine) to (after.inits - before.inits)
        }
        assertEquals(false to 0, traced(PerCall.OPERATION))
        assertEquals(false to 3, traced(PerCall.INIT_AND_OPERATION))
        assertEquals(true to 3, traced(PerCall.INSTANCE_INIT_AND_OPERATION))
    }

    @Test
    fun againReplaysTheLastDrawnCallOnANewInstanceWhenTheCallReinits() {
        fun replayed(perCall: PerCall): Triple<Boolean, Int, Int> {
            val seen = mutableListOf<Int>()
            val invocation = EngineCall({ Any() }, { _, n -> seen += n }, { it }).invocation(perCall)
            repeat(3) { invocation.once() }
            val held = invocation.trace!!
            val replayed = invocation.again()
            return Triple(replayed === held.engine, seen.last(), invocation.trace!!.inits - held.inits)
        }
        assertEquals(Triple(true, 0, 0), replayed(PerCall.OPERATION))
        assertEquals(Triple(false, 3, 0), replayed(PerCall.INIT_AND_OPERATION))
        assertEquals(Triple(false, 3, 0), replayed(PerCall.INSTANCE_INIT_AND_OPERATION))
    }

    // The timed lambda keeps master's state only: a check-only counter would run inside every timed call.
    @Test
    fun theTimedCallHoldsNoCheckOnlyState() {
        val fields = EngineCall::class.java.declaredFields.filterNot { it.isSynthetic }.map { it.name }.toSet()
        assertEquals(setOf("create", "init", "operate", "calls", "engine"), fields)
    }

    // The call counter passed to init is a primitive: no Integer per timed init once it passes the box cache.
    @Test
    fun aTimedInitAllocatesNoBoxedCounter() {
        val threads = ManagementFactory.getThreadMXBean() as com.sun.management.ThreadMXBean
        val invocation = EngineCall({ Any() }, { _, _ -> }, { null }).invocation(PerCall.INIT_AND_OPERATION)
        repeat(BOX_CACHE) { invocation.perIteration() }
        val before = threads.getThreadAllocatedBytes(Thread.currentThread().id)
        repeat(CALLS) { invocation.perIteration() }
        val perCall = (threads.getThreadAllocatedBytes(Thread.currentThread().id) - before).toDouble() / CALLS
        assertTrue("$perCall bytes per call", perCall < 1.0)
    }

    private companion object {
        const val BOX_CACHE = 128
        const val CALLS = 2_000
    }
}
