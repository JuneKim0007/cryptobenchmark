package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.interop.InteropOracle
import io.github.junekim0007.cryptobench.preparation.interop.plan.InteropPair
import io.github.junekim0007.cryptobench.preparation.interop.plan.InteropPlanFile
import io.github.junekim0007.cryptobench.preparation.interop.plan.Member
import io.github.junekim0007.cryptobench.preparation.interop.report.InteropFile
import io.github.junekim0007.cryptobench.preparation.interop.report.InteropVerdict
import io.github.junekim0007.cryptobench.preparation.port.Availability
import io.github.junekim0007.cryptobench.preparation.port.DeviceCapability
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test
import java.security.Security

class InteropOracleTest {

    private val jvm = object : DeviceCapability {
        override fun providers(): List<String> = Security.getProviders().map { it.name }
        override fun check(provider: String, type: String, algorithm: String): Availability {
            val parts = algorithm.split("/")
            val names = if (parts.size == 3) listOf(algorithm, "${parts[0]}/${parts[1]}", "${parts[0]}//${parts[2]}", parts[0]) else listOf(algorithm)
            val registered = names.any { Security.getProvider(provider)?.getService(type, it) != null }
            return if (registered) Availability.Available else Availability.Unavailable("not_registered")
        }
    }
    private val oracle = InteropOracle(jvm)

    private fun pair(type: String, provider: String, a: String, b: String, keySize: Int? = null, inputSize: Int? = null) =
        InteropPair(1, "g", Member(type, a, provider), Member(type, b, provider), keySize, inputSize)

    private fun verdict(p: InteropPair) = oracle.check(p).let { "${it.verdict}/${it.mode}" }

    @Test
    fun anOaepSpellingOfTheSameDefaultsIsCompatibleAndAnotherDigestIsNot() {
        assertEquals("compatible/produce_consume",
                     verdict(pair("Cipher", "SunJCE", "RSA/ECB/OAEPPadding", "RSA/ECB/OAEPWithSHA-1AndMGF1Padding", 2048)))
        val other = oracle.check(pair("Cipher", "SunJCE", "RSA/ECB/OAEPPadding", "RSA/ECB/OAEPWithSHA-256AndMGF1Padding", 2048))
        assertEquals(InteropVerdict.INCOMPATIBLE, other.verdict)
        assertTrue(other.reason, other.reason.contains("BadPaddingException"))
    }

    @Test
    fun aSymmetricCipherDecryptsWithTheParametersTheOtherSideChose() {
        assertEquals("compatible/produce_consume", verdict(pair("Cipher", "SunJCE", "AES/GCM/NoPadding", "AES/GCM/NoPadding", 128)))
    }

    @Test
    fun signaturesCrossVerifyOnlyForTheSameDigest() {
        assertEquals("compatible/produce_consume", verdict(pair("Signature", "SunRsaSign", "SHA256withRSA", "SHA256withRSA", 2048)))
        assertEquals("incompatible/produce_consume", verdict(pair("Signature", "SunRsaSign", "SHA256withRSA", "SHA512withRSA", 2048)))
    }

    @Test
    fun digestsAndMacsCompareOutputs() {
        assertEquals("compatible/same_output", verdict(pair("MessageDigest", "SUN", "SHA-256", "SHA-256", inputSize = 1024)))
        assertEquals("incompatible/same_output", verdict(pair("MessageDigest", "SUN", "SHA-256", "SHA-512")))
        assertEquals("compatible/same_output", verdict(pair("Mac", "SunJCE", "HmacSHA256", "HmacSHA256")))
    }

    @Test
    fun generatedKeysAndUnregisteredMembersAreNotTestable() {
        val keys = oracle.check(pair("KeyGenerator", "SunJCE", "AES", "AES", 128))
        assertEquals(InteropVerdict.NOT_TESTABLE, keys.verdict)
        assertTrue(keys.reason, keys.reason.contains("outputs_not_comparable"))
        val ghost = oracle.check(pair("Cipher", "SunJCE", "AES/GCM/NoPadding", "NOPE/GCM/NoPadding"))
        assertEquals(InteropVerdict.NOT_TESTABLE to InteropVerdict.NONE, ghost.verdict to ghost.mode)
        assertTrue(ghost.reason.contains("not_registered"))
    }

    @Test
    fun thePlanIsReadWholeAndRefusedByName() {
        val plan = mapOf("schemaVersion" to 1, "pairs" to listOf(mapOf(
            "id" to 3, "group" to "g", "keySize" to 2048,
            "a" to mapOf("type" to "Cipher", "algorithm" to "A", "provider" to "P1"),
            "b" to mapOf("type" to "Cipher", "algorithm" to "B", "provider" to "P2"))))
        assertEquals(listOf(InteropPair(3, "g", Member("Cipher", "A", "P1"), Member("Cipher", "B", "P2"), 2048, null)),
                     InteropPlanFile.parse(plan))
        val mixed = plan + ("pairs" to listOf(mapOf("id" to 1, "group" to "g",
            "a" to mapOf("type" to "Cipher", "algorithm" to "A", "provider" to "P"),
            "b" to mapOf("type" to "Mac", "algorithm" to "B", "provider" to "P"))))
        assertEquals("mixed_types: pair 1 joins Cipher and Mac at pairs[0]",
                     assertThrows(IllegalArgumentException::class.java) { InteropPlanFile.parse(mixed) }.message)
    }

    @Test
    fun verdictsBecomeTheInteropDocument() {
        val v = oracle.check(pair("MessageDigest", "SUN", "SHA-256", "SHA-512"))
        val doc = InteropFile.document(listOf(v), "interop_plan.yaml", "probe.yaml")
        @Suppress("UNCHECKED_CAST")
        val row = (doc["verdicts"] as List<Map<String, Any>>).single()
        assertEquals(mapOf("aToB" to "fail", "bToA" to "fail"), row["directions"])
        assertEquals("incompatible", row["verdict"])
    }
}
