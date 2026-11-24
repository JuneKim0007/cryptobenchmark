package io.github.junekim0007.cryptobench.discovery.trial.call

import io.github.junekim0007.cryptobench.document.catalogue.FamilyCatalogue
import org.junit.Assert.assertEquals
import org.junit.Test

/** A catalogued service's generators of its key type, then that key type, with the names file's key size, then with the entry's key spec; an uncatalogued one only the generic names. */
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
    fun aPssSignatureTakesThePssGeneratorAndAnRsaSignatureTheRsaOne() {
        assertEquals(listOf("RSASSA-PSS"), candidates.of("Signature", "RSASSA-PSS", "SunRsaSign").map { it.name }.distinct())
        assertEquals(listOf("RSA"), candidates.of("Signature", "SHA256withRSA", "SunRsaSign").map { it.name }.distinct())
        for (provider in listOf("AndroidOpenSSL", "BundledConscrypt")) {
            assertEquals(provider, listOf("RSA"), candidates.of("Signature", "SHA256withRSA/PSS", provider).map { it.name }.distinct())
        }
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
    fun anEntrysKeyGenerationSpecFollowsTheNameAlone() {
        val gost = candidates.of("Signature", "GOST3411-2012-512WITHECGOST3410-2012-512", "BundledBC")
        assertEquals(listOf("ECGOST3410-2012" to null, "ECGOST3410-2012" to "jca.ecGenSpec[Tc26-Gost-3410-12-512-paramSetA]"), gost.map { it.name to it.spec?.label })
        assertEquals("Tc26-Gost-3410-12-512-paramSetA", (gost.last().spec!!.spec as java.security.spec.ECGenParameterSpec).name)
        assertEquals(emptyList<KeyGenerationSpec.Built>(), candidates.of("KeyAgreement", "DH", "SunJCE").mapNotNull { it.spec })
    }

    @Test
    fun aRawKeyTakesTheEntrysKeyTypeElseTheLongestRegisteredNameContained() {
        assertEquals("AES", candidates.raw("Cipher", "AES/GCM/NoPadding", "SunJCE"))
        assertEquals("Unlisted", candidates.raw("Cipher", "UnlistedAES/X/Y", "SunJCE"))
        assertEquals("Nothing/X/Y", candidates.raw("Cipher", "Nothing/X/Y", "SunJCE"))
    }
}
