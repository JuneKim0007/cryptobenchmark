package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.parameter.bind.BoundParameters
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import javax.crypto.spec.IvParameterSpec

class BoundParametersTest {

    @Test
    fun cyclingGivesTheFixedSpecsInTurnAndVariesOnlyWithMoreThanOne() {
        val first = IvParameterSpec(ByteArray(16))
        val second = IvParameterSpec(ByteArray(16) { 1 })
        val cycling = BoundParameters.cycling(listOf(first, second))
        assertTrue(cycling.varies)
        assertEquals(listOf(first, second, first), List(3) { cycling.next() })
        assertFalse(BoundParameters.cycling(listOf(first)).varies)
    }
}
