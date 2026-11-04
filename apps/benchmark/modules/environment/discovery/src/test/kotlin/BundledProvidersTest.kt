package io.github.junekim0007.cryptobench.discovery

import io.github.junekim0007.cryptobench.discovery.bundled.BundledProvider
import io.github.junekim0007.cryptobench.discovery.bundled.BundledProviderException
import io.github.junekim0007.cryptobench.discovery.bundled.BundledProviders
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertThrows
import org.junit.Test

class BundledProvidersTest {

    @Test
    fun readsTheListAndSplitsTheFactory() {
        val read = BundledProviders.read(mapOf(BundledProviders.KEY to listOf(
            mapOf("artifact" to "a:b:1", "create" to "a.b.Provider"),
            mapOf("artifact" to "c:d:2", "create" to "c.d.Outer\$Inner#make", "alias" to "D"),
        )))

        assertEquals(listOf(BundledProvider("a:b:1", "a.b.Provider"), BundledProvider("c:d:2", "c.d.Outer\$Inner#make", "D")), read)
        assertNull(read[0].factory)
        assertEquals("c.d.Outer\$Inner", read[1].className)
        assertEquals("make", read[1].factory)
    }

    @Test
    fun anAbsentKeyIsNoBundledProvider() {
        assertEquals(emptyList<BundledProvider>(), BundledProviders.read(mapOf("run" to emptyMap<String, Any>())))
    }

    @Test
    fun refusesAndNamesWhatIsWrong() {
        val cases = listOf(
            "wrong_type" to "not a list",
            "missing_field" to listOf(mapOf("artifact" to "a:b:1")),
            "unknown_keys" to listOf(mapOf("artifact" to "a:b:1", "create" to "a.B", "position" to 1)),
            "invalid_create" to listOf(mapOf("artifact" to "a:b:1", "create" to "a.B#")),
            "invalid_create" to listOf(mapOf("artifact" to "a:b:1", "create" to "a..B")),
            "blank_alias" to listOf(mapOf("artifact" to "a:b:1", "create" to "a.B", "alias" to " ")),
        )
        cases.forEach { (code, value) ->
            val error = assertThrows(BundledProviderException::class.java) { BundledProviders.read(mapOf(BundledProviders.KEY to value)) }
            assertEquals(code, error.code)
        }
    }
}
