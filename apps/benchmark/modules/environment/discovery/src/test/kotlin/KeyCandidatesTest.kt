package io.github.junekim0007.cryptobench.discovery.trial.call

import io.github.junekim0007.cryptobench.document.catalogue.FamilyCatalogue
import org.junit.Assert.assertEquals
import org.junit.Test

/** A catalogued service's generators of its key type, then that key type, with the names file's key size; an uncatalogued one only the generic names. */
class KeyCandidatesTest {

    private val catalogue = FamilyCatalogue.bundled(FamilyCatalogue.KEYED + FamilyCatalogue.GENERATORS)

    private val candidates = KeyCandidates(catalogue, "jdk-25", listOf("AES", "EC", "HmacSHA256", "Unlisted").map { "KeyGenerator" to it } + ("KeyGenerator" to "ARC4"))

    private fun names(type: String, algorithm: String) = candidates.of(type, algorithm, "SunJCE").map { it.name to it.size }

    @Test
    fun aCataloguedServiceTriesItsKeyTypesGeneratorsFirst() {
        assertEquals("AES" to null, names("Cipher", "AES/GCM/NoPadding").first())
        assertEquals("AES" to 128, names("Cipher", "AES_128/GCM/NoPadding").first())
        assertEquals(listOf("ChaCha20" to 256, "ChaCha20" to null), names("Cipher", "ChaCha20-Poly1305").take(2))
        assertEquals(listOf(true, false), candidates.of("Cipher", "AES_128/GCM/NoPadding", "SunJCE").take(1).map { it.fixed } + candidates.of("Cipher", "ChaCha20-Poly1305", "SunJCE").take(1).map { it.fixed })
        assertEquals("EC" to null, names("Signature", "SHA256withECDSA").first())
        assertEquals("EC" to null, names("KeyAgreement", "ECDH").first())
        assertEquals("HmacSHA256" to null, names("Mac", "HmacSHA256").first())
    }

    @Test
    fun aGeneratorIsFollowedByTheRegisteredSpellingsOfIt() {
        assertEquals(listOf("ARCFOUR", "ARC4"), names("Cipher", "ARC4").map { it.first }.take(2))
    }

    @Test
    fun aCataloguedServiceTriesNoNameItsEntryDoesNotGive() {
        assertEquals(emptyList<String>(), names("Cipher", "AES/GCM/NoPadding").map { it.first }.filter { it == "AES/GCM/NoPadding" || it == "Unlisted" })
        assertEquals(listOf("PBEWITHMD5AND128BITAES-CBC-OPENSSL" to null), names("Cipher", "PBEWITHMD5AND128BITAES-CBC-OPENSSL"))
    }

    @Test
    fun anUncataloguedServiceTriesItsNameThenTheRegisteredNamesItContains() {
        assertEquals(listOf("UnlistedAES/X/Y" to null, "Unlisted" to null, "AES" to null), names("Cipher", "UnlistedAES/X/Y"))
    }

    @Test
    fun aRawKeyTakesTheEntrysKeyTypeElseTheLongestRegisteredNameContained() {
        assertEquals("AES", candidates.raw("Cipher", "AES/GCM/NoPadding", "SunJCE"))
        assertEquals("Unlisted", candidates.raw("Cipher", "UnlistedAES/X/Y", "SunJCE"))
        assertEquals("Nothing/X/Y", candidates.raw("Cipher", "Nothing/X/Y", "SunJCE"))
    }
}
