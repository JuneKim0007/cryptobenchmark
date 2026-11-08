package io.github.junekim0007.cryptobench.jca

import io.github.junekim0007.cryptobench.jca.failure.Attempt
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

/** The one catch rule every module shares: an Exception or a LinkageError is the attempt's result, any other Error escapes. */
class AttemptTest {

    @Test
    fun anExceptionOrALinkageErrorIsTheResult() {
        assertEquals("boom", Attempt.of { throw IllegalStateException("boom") }.exceptionOrNull()?.message)
        assertEquals("org/missing/Helper", Attempt.of { throw NoClassDefFoundError("org/missing/Helper") }.exceptionOrNull()?.message)
        assertEquals(1, Attempt.of { 1 }.getOrNull())
    }

    @Test
    fun anyOtherErrorEscapes() {
        assertThrows(AssertionError::class.java) { Attempt.of { throw AssertionError("provider bug") } }
        assertThrows(StackOverflowError::class.java) { Attempt.of { deep(0) } }
        assertThrows(OutOfMemoryError::class.java) { Attempt.of { throw OutOfMemoryError("heap") } }
    }

    private fun deep(n: Int): Int = deep(n + 1) + 1
}
