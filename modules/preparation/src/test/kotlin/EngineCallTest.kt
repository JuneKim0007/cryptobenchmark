package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.operation.EngineCall
import io.github.junekim0007.cryptobench.preparation.operation.PerCall
import org.junit.Assert.assertEquals
import org.junit.Test

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
}
