package io.github.junekim0007.cryptobench.discovery

import io.github.junekim0007.cryptobench.discovery.contract.CapturedEnvironment
import io.github.junekim0007.cryptobench.discovery.contract.ProviderEntry
import io.github.junekim0007.cryptobench.discovery.contract.RuntimeInfo
import io.github.junekim0007.cryptobench.discovery.contract.ServiceAttributes
import io.github.junekim0007.cryptobench.discovery.contract.ServiceEntry
import io.github.junekim0007.cryptobench.discovery.query.CaptureQuery
import io.github.junekim0007.cryptobench.discovery.query.ServiceShape
import org.junit.Assert.assertEquals
import org.junit.Test

class CaptureQueryTest {

    private val first = ProviderEntry(
        name = "First", precedence = 1,
        services = listOf(
            ServiceEntry("Cipher", "AES", "a.Aes", aliases = listOf("Rijndael"),
                attributes = ServiceAttributes.of(mapOf("SupportedModes" to listOf("ECB", "CBC"), "SupportedPaddings" to listOf("NOPADDING")))),
            ServiceEntry("MessageDigest", "SHA-256", "a.Sha"),
        ),
    )

    private val second = ProviderEntry(
        name = "Second", precedence = 2,
        services = listOf(
            ServiceEntry("Cipher", "aes", "b.Aes", aliases = listOf("2.16.840.1.101.3.4.1"),
                attributes = ServiceAttributes.of(mapOf("SupportedModes" to listOf("CBC", "GCM"), "SupportedPaddings" to listOf("NOPADDING", "PKCS5PADDING")))),
            ServiceEntry("Mac", "HmacSHA256", "b.Hmac"),
        ),
    )

    private val query = CaptureQuery(CapturedEnvironment(RuntimeInfo.unknown(), listOf(second, first)))

    /** Precedence decides who answers an unqualified getInstance, whatever order the entries came in. */
    @Test
    fun whoServesIsOrderedByPrecedenceAndReachesThroughAliases() {
        assertEquals(listOf("First", "Second"), query.whoServes("cipher", "AES").map { it.name })
        assertEquals(listOf("First"), query.whoServes("Cipher", "rijndael").map { it.name })
        assertEquals(listOf("Second"), query.whoServes("Cipher", "2.16.840.1.101.3.4.1").map { it.name })
        assertEquals(emptyList<String>(), query.whoServes("Cipher", "DES").map { it.name })
    }

    @Test
    fun serviceOfReturnsTheRegisteredSpelling() {
        assertEquals("aes", query.serviceOf("Second", "Cipher", "2.16.840.1.101.3.4.1")?.algorithm)
        assertEquals(null, query.serviceOf("Second", "Cipher", "Rijndael"))
        assertEquals(null, query.serviceOf("Nobody", "Cipher", "AES"))
    }

    @Test
    fun namesOfUnionsTheRegisteredNamesAndAliasesAcrossProviders() {
        assertEquals(setOf("AES", "Rijndael", "aes", "2.16.840.1.101.3.4.1"), query.namesOf("Cipher", "aes"))
    }

    @Test
    fun onlyOnListsWhatNobodyElseRegisters() {
        assertEquals(listOf("SHA-256"), query.onlyOn("First").map { it.algorithm })
        assertEquals(listOf("HmacSHA256"), query.onlyOn("Second").map { it.algorithm })
        assertEquals(emptyList<ServiceEntry>(), query.onlyOn("Nobody"))
    }

    /** One node per (type, algorithm) however it is spelled; modes and paddings unioned in declaration order. */
    @Test
    fun treeMergesSpellingsAndUnionsDeclaredModes() {
        val tree = query.tree()
        assertEquals(listOf("Cipher", "Mac", "MessageDigest"), tree.keys.toList())
        assertEquals(
            ServiceShape(modes = listOf("ECB", "CBC", "GCM"), paddings = listOf("NOPADDING", "PKCS5PADDING"), providers = listOf("First", "Second")),
            tree.getValue("Cipher").getValue("AES"),
        )
        assertEquals(listOf("AES"), tree.getValue("Cipher").keys.toList())
    }
}
