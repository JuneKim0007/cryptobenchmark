package io.github.junekim0007.cryptobench.discovery

import io.github.junekim0007.cryptobench.contract.bundled.BundledProvider
import io.github.junekim0007.cryptobench.discovery.bundled.BundledProviders
import io.github.junekim0007.cryptobench.document.DocumentFields
import io.github.junekim0007.cryptobench.document.YamlCodec
import io.github.junekim0007.cryptobench.files.RepositoryFiles
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

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

    // tests/contracts/documents/bundled-cases.json, each providers.bundled as bundledProviders; the cases about the providers section itself are config's
    @Test
    fun eachSharedCaseIsRefusedWithConfigsCodeOrAccepted() {
        val cases = DocumentFields.sections(YamlCodec.DOCUMENT.load(File(RepositoryFiles.documents, "bundled-cases.json").readText()), "cases")
        val entryCases = cases.filter { it["providers"] == null || (it["providers"] as? Map<*, *>)?.keys == setOf("bundled") }
        val mismatches = entryCases.mapNotNull { case ->
            val document = (case["providers"] as Map<*, *>?)?.let { mapOf(BundledProviders.KEY to it["bundled"]) }.orEmpty()
            @Suppress("UNCHECKED_CAST")
            val code = try {
                BundledProviders.read(document as Map<String, Any>)
                null
            } catch (refused: IllegalArgumentException) {
                refused.message!!.substringBefore(':')
            }
            "${case["name"]}: expected ${case["code"]}, got $code".takeIf { code != case["code"] }
        }
        assertTrue(entryCases.size > cases.size / 2)
        assertEquals(emptyList<String>(), mismatches)
    }
}
