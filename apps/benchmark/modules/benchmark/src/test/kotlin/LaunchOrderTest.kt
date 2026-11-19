package io.github.junekim0007.cryptobench.benchmark

import io.github.junekim0007.cryptobench.benchmark.check.LaunchOrder
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

/** The order file is taken only when it names every listed case once; anything else is order_mismatch, never the listing's order. */
class LaunchOrderTest {

    private val listed = listOf("a", "b", "c")

    @Test
    fun aPermutationIsTheOrder() {
        assertEquals(listOf("c", "a", "b"), LaunchOrder.of(listed, "c\na\nb\n"))
    }

    @Test
    fun aMissingExtraRepeatedOrEmptyOrderIsRefused() {
        val refused = { text: String -> assertThrows(IllegalStateException::class.java) { LaunchOrder.of(listed, text) }.message }
        assertEquals("order_mismatch: 2 ids for 3 listed cases; not listed [], missing [c]", refused("a\nb\n"))
        assertEquals("order_mismatch: 3 ids for 3 listed cases; not listed [x], missing [c]", refused("a\nb\nx\n"))
        assertEquals("order_mismatch: 3 ids for 3 listed cases; not listed [], missing [c]", refused("a\nb\nb\n"))
        assertEquals("order_mismatch: 0 ids for 3 listed cases; not listed [], missing [a, b, c]", refused(""))
    }
}
