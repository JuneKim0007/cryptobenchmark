package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.interop.InteropOracle
import io.github.junekim0007.cryptobench.preparation.interop.InteropRun
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
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
import org.yaml.snakeyaml.Yaml
import java.security.AlgorithmParameters
import java.security.Key
import java.security.PrivateKey
import java.security.Provider
import java.security.PublicKey
import java.security.SecureRandom
import java.security.Security
import java.security.Signature
import java.security.SignatureSpi
import java.security.spec.AlgorithmParameterSpec
import java.security.spec.MGF1ParameterSpec
import java.security.spec.PSSParameterSpec
import javax.crypto.Cipher
import javax.crypto.CipherSpi
import javax.crypto.spec.OAEPParameterSpec
import javax.crypto.spec.PSource

// SunJCE's OAEPWithSHA-256AndMGF1Padding keeps MGF1 on SHA-1; this one moves MGF1 to SHA-256, as other providers do.
class Mgf1Sha256Oaep : CipherSpi() {
    private val inner = Cipher.getInstance("RSA/ECB/OAEPPadding", "SunJCE")
    private val spec = OAEPParameterSpec("SHA-256", "MGF1", MGF1ParameterSpec.SHA256, PSource.PSpecified.DEFAULT)

    override fun engineSetMode(mode: String?) {}
    override fun engineSetPadding(padding: String?) {}
    override fun engineGetBlockSize(): Int = inner.blockSize
    override fun engineGetOutputSize(inputLen: Int): Int = inner.getOutputSize(inputLen)
    override fun engineGetIV(): ByteArray? = null
    override fun engineGetParameters(): AlgorithmParameters? = null
    override fun engineInit(opmode: Int, key: Key, random: SecureRandom?) = inner.init(opmode, key, spec, random)
    override fun engineInit(opmode: Int, key: Key, params: AlgorithmParameterSpec?, random: SecureRandom?) = inner.init(opmode, key, spec, random)
    override fun engineInit(opmode: Int, key: Key, params: AlgorithmParameters?, random: SecureRandom?) = inner.init(opmode, key, spec, random)
    override fun engineUpdate(input: ByteArray?, offset: Int, length: Int): ByteArray? =
        if (input == null) null else inner.update(input, offset, length)
    override fun engineUpdate(input: ByteArray?, offset: Int, length: Int, output: ByteArray?, outputOffset: Int): Int =
        if (input == null) 0 else inner.update(input, offset, length, output, outputOffset)
    override fun engineDoFinal(input: ByteArray?, offset: Int, length: Int): ByteArray =
        if (input == null) inner.doFinal() else inner.doFinal(input, offset, length)
    override fun engineDoFinal(input: ByteArray?, offset: Int, length: Int, output: ByteArray?, outputOffset: Int): Int =
        if (input == null) inner.doFinal(output, outputOffset) else inner.doFinal(input, offset, length, output, outputOffset)
}

const val PSS_NAME = "SHA256withRSA/PSS"

// SunRsaSign's RSASSA-PSS has no default parameters; this one fixes them, as a provider naming the digest does.
class FixedPss : SignatureSpi() {
    private val inner = Signature.getInstance("RSASSA-PSS", "SunRsaSign")
    private val spec = PSSParameterSpec("SHA-256", "MGF1", MGF1ParameterSpec.SHA256, 32, 1)

    override fun engineInitVerify(key: PublicKey) { inner.setParameter(spec); inner.initVerify(key) }
    override fun engineInitSign(key: PrivateKey) { inner.setParameter(spec); inner.initSign(key) }
    override fun engineUpdate(b: Byte) = inner.update(b)
    override fun engineUpdate(b: ByteArray, off: Int, len: Int) = inner.update(b, off, len)
    override fun engineSign(): ByteArray = inner.sign()
    override fun engineVerify(sig: ByteArray): Boolean = inner.verify(sig)
    @Deprecated("the JCA abstract member") override fun engineSetParameter(param: String?, value: Any?) = Unit
    @Deprecated("the JCA abstract member") override fun engineGetParameter(param: String?): Any? = null
}

class InteropOracleTest {

    @get:Rule
    val folder = TemporaryFolder()

    private val jvm = object : DeviceCapability {
        override fun providers(): List<String> = Security.getProviders().map { it.name }
        override fun check(provider: String, type: String, algorithm: String): Availability {
            val parts = algorithm.split("/")
            val names = if (parts.size == 3) listOf(algorithm, "${parts[0]}/${parts[1]}", "${parts[0]}//${parts[2]}", parts[0]) else listOf(algorithm)
            val registered = names.any { Security.getProvider(provider)?.getService(type, it) != null }
            return if (registered) Availability.Available else Availability.Unavailable("not_registered")
        }
        override fun measuredKeyAlgorithm(provider: String, type: String, algorithm: String): String? =
            if (algorithm == PSS_NAME) "RSA" else null
    }
    private val oracle = InteropOracle(jvm)

    private fun pair(type: String, provider: String, a: String, b: String, keySize: Int? = null, inputSize: Int? = null) =
        InteropPair(1, "g", Member(type, a, provider), Member(type, b, provider), keySize, inputSize)

    private fun verdict(p: InteropPair) = oracle.check(p).let { "${it.result}/${it.mode}" }

    private fun <T> withFakeOaep(block: () -> T): T {
        val fake = object : Provider("FakeOaep", "1", "MGF1 on the OAEP digest") {
            init { put("Cipher.RSA/ECB/OAEPWithSHA-256AndMGF1Padding", Mgf1Sha256Oaep::class.java.name) }
        }
        Security.addProvider(fake)
        try {
            return block()
        } finally {
            Security.removeProvider(fake.name)
        }
    }

    private fun withFakePss(block: () -> Unit) {
        val fake = object : Provider("FakePss", "1", "PSS at fixed parameters") {
            init { put("Signature.$PSS_NAME", FixedPss::class.java.name) }
        }
        Security.addProvider(fake)
        try {
            block()
        } finally {
            Security.removeProvider(fake.name)
        }
    }

    @Test
    fun anOaepSpellingOfTheSameDefaultsPassesAndAnotherDigestFails() {
        assertEquals("pass/produce_consume",
                     verdict(pair("Cipher", "SunJCE", "RSA/ECB/OAEPPadding", "RSA/ECB/OAEPWithSHA-1AndMGF1Padding", 2048)))
        val other = oracle.check(pair("Cipher", "SunJCE", "RSA/ECB/OAEPPadding", "RSA/ECB/OAEPWithSHA-256AndMGF1Padding", 2048))
        assertEquals(InteropVerdict.FAIL, other.result)
        assertTrue(other.reason, other.reason.contains("BadPaddingException"))
    }

    @Test
    fun theSameOaepNameFailsAcrossProvidersWhoseMgf1DigestsDiffer() {
        val name = "RSA/ECB/OAEPWithSHA-256AndMGF1Padding"
        val v = withFakeOaep {
            oracle.check(InteropPair(1, "g", Member("Cipher", name, "SunJCE"), Member("Cipher", name, "FakeOaep"), 2048, null))
        }
        assertEquals(InteropVerdict.FAIL to InteropVerdict.PRODUCE_CONSUME, v.result to v.mode)
        assertEquals("fail" to "fail", v.aToB.label to v.bToA.label)
    }

    @Test
    fun aSymmetricCipherDecryptsWithTheParametersTheOtherSideChose() {
        assertEquals("pass/produce_consume", verdict(pair("Cipher", "SunJCE", "AES/GCM/NoPadding", "AES/GCM/NoPadding", 128)))
    }

    @Test
    fun signaturesCrossVerifyOnlyForTheSameDigest() {
        assertEquals("pass/produce_consume", verdict(pair("Signature", "SunRsaSign", "SHA256withRSA", "SHA256withRSA", 2048)))
        assertEquals("fail/produce_consume", verdict(pair("Signature", "SunRsaSign", "SHA256withRSA", "SHA512withRSA", 2048)))
    }

    // Each call's bytes differ: the mode comes from the type's operations, so these pass by crossing, never by equality.
    @Test
    fun randomizedOutputsCrossVerifyOrCrossDecrypt() {
        assertEquals("pass/produce_consume", verdict(pair("Signature", "SunEC", "SHA256withECDSA", "SHA256withECDSA", 256)))
        withFakePss { assertEquals("pass/produce_consume", verdict(pair("Signature", "FakePss", PSS_NAME, PSS_NAME, 2048))) }
        assertEquals("pass/produce_consume", verdict(pair("Cipher", "SunJCE", "RSA/ECB/OAEPPadding", "RSA/ECB/OAEPPadding", 2048)))
        assertEquals("pass/produce_consume", verdict(pair("Cipher", "SunJCE", "AES/GCM/NoPadding", "AES/GCM/NoPadding", 128)))
    }

    @Test
    fun digestsAndMacsCompareOutputs() {
        assertEquals("pass/same_output", verdict(pair("MessageDigest", "SUN", "SHA-256", "SHA-256", inputSize = 1024)))
        assertEquals("fail/same_output", verdict(pair("MessageDigest", "SUN", "SHA-256", "SHA-512")))
        assertEquals("pass/same_output", verdict(pair("Mac", "SunJCE", "HmacSHA256", "HmacSHA256")))
    }

    @Test
    fun generatedKeysAndUnregisteredMembersAreNotCheckable() {
        val keys = oracle.check(pair("KeyGenerator", "SunJCE", "AES", "AES", 128))
        assertEquals(InteropVerdict.NOT_CHECKABLE, keys.result)
        assertTrue(keys.reason, keys.reason.contains("outputs_not_comparable"))
        val ghost = oracle.check(pair("Cipher", "SunJCE", "AES/GCM/NoPadding", "NOPE/GCM/NoPadding"))
        assertEquals(InteropVerdict.NOT_CHECKABLE to InteropVerdict.NONE, ghost.result to ghost.mode)
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
        val row = (doc["pairs"] as List<Map<String, Any>>).single()
        assertEquals(mapOf("aToB" to "fail", "bToA" to "fail"), row["directions"])
        assertEquals("fail", row["result"])
        assertEquals(mapOf("type" to "MessageDigest", "algorithm" to "SHA-512", "provider" to "SUN"), row["b"])
    }

    @Test
    fun aPlanFileRunsIntoAnInteropFile() {
        val plan = folder.newFile("interop_plan.yaml").apply {
            writeText("schemaVersion: 1\npairs:\n- {id: 7, group: g, a: {type: Mac, algorithm: HmacSHA256, provider: SunJCE}, " +
                      "b: {type: Mac, algorithm: HmacSHA256, provider: SunJCE}}\n")
        }
        val out = folder.root.resolve("out/interop.yaml")
        InteropRun.run(jvm, plan, folder.newFile("probe_x.yaml"), out)
        @Suppress("UNCHECKED_CAST")
        val doc = Yaml().load<Map<String, Any>>(out.readText())
        assertEquals(mapOf("plan" to "interop_plan.yaml", "capture" to "probe_x.yaml"), doc["generatedFrom"])
        @Suppress("UNCHECKED_CAST")
        assertEquals(listOf(7 to "pass"), (doc["pairs"] as List<Map<String, Any>>).map { it["id"] to it["result"] })
    }
}
