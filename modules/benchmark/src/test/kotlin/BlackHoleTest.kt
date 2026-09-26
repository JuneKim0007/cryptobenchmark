package io.github.junekim0007.cryptobench.benchmark

import io.github.junekim0007.cryptobench.benchmark.run.BlackHole
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.lang.reflect.Modifier

/**
 * The sink exists so the JIT cannot prove a timed call's result unused and delete the call. That needs
 * the value stored in a static field nobody reads: a reader is what would let the field be optimised
 * back out, and a second way in is what would let a caller store a value the field never keeps.
 */
class BlackHoleTest {

    @Test
    fun theOnlyWayIntoTheSinkIsConsume() {
        assertEquals(listOf("consume"), BlackHole::class.java.declaredMethods.map { method -> method.name }.sorted())
        val field = BlackHole::class.java.getDeclaredField("last")
        assertTrue("modifiers ${field.modifiers}", Modifier.isStatic(field.modifiers) && Modifier.isPrivate(field.modifiers))
    }
}
