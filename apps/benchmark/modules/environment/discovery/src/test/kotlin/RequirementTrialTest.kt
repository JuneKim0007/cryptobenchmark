package io.github.junekim0007.cryptobench.discovery

import io.github.junekim0007.cryptobench.discovery.adapter.ProviderProbe
import io.github.junekim0007.cryptobench.discovery.contract.ServiceRequirement
import io.github.junekim0007.cryptobench.discovery.trial.DefaultRunTrial
import io.github.junekim0007.cryptobench.discovery.trial.TrialRunner
import io.github.junekim0007.cryptobench.discovery.trial.call.DefaultKeys
import io.github.junekim0007.cryptobench.discovery.contract.ErrorText
import io.github.junekim0007.cryptobench.discovery.contract.ServiceTrialEntry
import io.github.junekim0007.cryptobench.discovery.contract.TrialOutcome
import io.github.junekim0007.cryptobench.discovery.trial.requirement.AliasRuns
import io.github.junekim0007.cryptobench.discovery.trial.requirement.CallResult
import io.github.junekim0007.cryptobench.discovery.trial.requirement.KeyOrigin
import io.github.junekim0007.cryptobench.discovery.trial.requirement.KeySources
import io.github.junekim0007.cryptobench.discovery.trial.requirement.ProbedService
import io.github.junekim0007.cryptobench.discovery.trial.requirement.RequirementTrial
import io.github.junekim0007.cryptobench.discovery.write.ProbeDirectory
import io.github.junekim0007.cryptobench.discovery.write.RequirementDocument
import io.github.junekim0007.cryptobench.discovery.write.RequirementYamlWriter
import io.github.junekim0007.cryptobench.discovery.write.YamlCodec
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.nio.file.Files
import java.security.Key
import java.security.Provider
import java.security.SecureRandom
import java.security.Security
import java.security.spec.AlgorithmParameterSpec
import java.security.spec.KeySpec
import javax.crypto.CipherSpi
import javax.crypto.KeyGeneratorSpi
import javax.crypto.Mac
import javax.crypto.MacSpi
import javax.crypto.SecretKey
import javax.crypto.SecretKeyFactorySpi
import javax.crypto.spec.SecretKeySpec
import java.security.InvalidKeyException
import java.security.AlgorithmParameters

/** Against the live JVM's providers, plus made-up ones that refuse or misbehave. */
class RequirementTrialTest {

    private fun report(providers: Array<Provider>) = run {
        val capture = ProviderProbe().capture(providers)
        val keys = DefaultKeys(providers.toList())
        RequirementTrial().run(capture, DefaultRunTrial().run(TrialRunner().run(capture, providers), providers, keys), providers, keys)
    }

    private fun jvm(provider: String, type: String, algorithm: String): ServiceRequirement =
        JVM.services.single { it.provider == provider && it.type == type && it.algorithm.equals(algorithm, ignoreCase = true) }

    @Suppress("UNCHECKED_CAST")
    private fun fact(service: ServiceRequirement, name: String): Map<String, Any> = service.facts.getValue(name) as Map<String, Any>

    @Test
    fun everyRegisteredServiceHasARecordOrACodedReason() {
        val registered = CAPTURE.providers.sumOf { it.services.size }
        assertEquals(registered, JVM.services.count { it.transformationOf.isEmpty() })
        assertTrue(JVM.services.all { it.status == ServiceRequirement.RUNNABLE || it.reason.isNotEmpty() })
    }

    @Test
    fun measuresWhatADefaultRunCannot() {
        val gcm = jvm("SunJCE", "Cipher", "AES/GCM/NoPadding")
        assertEquals(ServiceRequirement.RUNNABLE, gcm.status)
        assertEquals("96,104,112,120,128", fact(gcm, "tagBits")["accepted"])
        assertEquals("16,24,32", fact(gcm, "keyBytes")["accepted"])
        assertEquals(true, fact(gcm, "reuseGuard")["refused"])
        @Suppress("UNCHECKED_CAST")
        assertEquals(false, (fact(gcm, "reuseGuard")["newInstance"] as Map<String, Any>)["refused"])
        assertEquals(true, gcm.facts["roundTrip"])
        assertEquals("refused AEADBadTagException", gcm.facts["tamper"])
        assertEquals(true, fact(gcm, "aad")["supported"])
        assertTrue(fact(gcm, "inputBytes")["outputBytes"].toString(), " 16:32 " in fact(gcm, "inputBytes")["outputBytes"].toString())
        val ctr = jvm("SunJCE", "Cipher", "AES/CTR/NoPadding")
        assertEquals("accepted, altered plaintext", ctr.facts["tamper"])
        assertEquals(true, ctr.facts["deterministicFixed"])
        assertEquals(false, ctr.facts["deterministicGenerated"])
    }

    @Test
    fun aPasswordBasedCipherRunsOnAKeyFromItsFactory() {
        val pbe = jvm("SunJCE", "Cipher", "PBEWithHmacSHA256AndAES_256")
        assertEquals(ServiceRequirement.RUNNABLE, pbe.status)
        assertEquals("SecretKeyFactory", pbe.key["source"])
        assertEquals(true, pbe.facts["roundTrip"])
    }

    @Test
    fun aProviderThatRefusesEverySoftwareKeyIsKeystoreBorn() {
        val providers = Security.getProviders() + Bound()
        val bound = report(providers).services.filter { it.provider == "Bound" }
        assertEquals(2, bound.size)
        assertTrue(bound.toString(), bound.all { it.status == ServiceRequirement.NOT_RUNNABLE && it.reason == ServiceRequirement.KEYSTORE_BORN_KEY })
        assertTrue(bound.all { ServiceRequirement.KEYSTORE_BORN_CONDITION in it.conditions })
        assertTrue(bound.toString(), bound.all { it.measuredReason in setOf(ServiceRequirement.KEY_REFUSED, ServiceRequirement.GENERATION_REFUSED, ServiceRequirement.NO_KEY) })
    }

    @Test
    fun aProviderWithNoGeneratorOfItsOwnIsBoundEvenWhenOneOfItsServicesRuns() {
        fun record(provider: String, status: String, reason: String) = ServiceRequirement(provider, "Cipher", "A", status, reason = reason)
        val applied = KeyOrigin.applied(
            listOf(
                record("NoGenerator", ServiceRequirement.RUNNABLE, ""),
                record("NoGenerator", ServiceRequirement.NOT_RUNNABLE, ServiceRequirement.KEY_REFUSED),
                ServiceRequirement("Generates", "KeyGenerator", "A", ServiceRequirement.RUNNABLE),
                record("Generates", ServiceRequirement.NOT_RUNNABLE, ServiceRequirement.KEY_REFUSED),
            ),
        )
        assertEquals(listOf("", ServiceRequirement.KEYSTORE_BORN_KEY, "", ServiceRequirement.KEY_REFUSED), applied.map { it.reason })
        assertEquals(listOf("", ServiceRequirement.KEY_REFUSED, "", ""), applied.map { it.measuredReason })
    }

    @Test
    fun aKeyFingerprintGoesWithTheOtherKeyMaterial() {
        val text = ErrorText.clean("Key: DH Private Key [6e:4e:cc:01:3c:c2:30:81:60:ce:63:4c:f8:fb:6d:34:75:0f:39:74] rest")
        assertEquals("Key: DH Private Key [<removed>] rest", text)
    }

    @Test
    fun aCallThatThrowsAnythingIsRecordedAndNeverAborts() {
        val thrown = report(Security.getProviders() + Throwing()).services.single { it.provider == "Throwing" }
        assertEquals(ServiceRequirement.NOT_RUNNABLE, thrown.status)
        assertTrue(thrown.detail, thrown.detail.length <= 200)
        assertTrue("key material left in: " + thrown.detail, "1234567890123456" !in thrown.detail)
    }

    @Test
    fun anAliasWhoseRecordFailsIsRecordedAloneBesideTheOthers() {
        val aliased = Aliased()
        val live = listOf<Provider>(aliased)
        val capture = ProviderProbe().capture(arrayOf(aliased))
        val entry = capture.providers.single().services.single { it.type == "Mac" }
        val trial = ServiceTrialEntry(aliased.name, entry.type, entry.algorithm, TrialOutcome.SUCCESS)
        val service = ProbedService(aliased, entry.type, entry.algorithm, entry, trial, KeySources(capture, live, DefaultKeys(live)), live, emptyList(), emptyList())
        val aliases = AliasRuns.of(service, HmacTag::class.java.name, CallResult(aliasRuns = {}, aliasAcceptsKey = { _, _ -> }))
        assertEquals(listOf("TAG-A", "TAG-B"), aliases.map { it["name"] })
        assertEquals("same", aliases.single { it["name"] == "TAG-A" }["behaviour"])
        assertEquals(mapOf("name" to "TAG-B", "error" to "IllegalStateException: no encoding"), aliases.single { it["name"] == "TAG-B" })
    }

    @Test
    fun aKeyWhoseEncodingThrowsFailsItsOwnServiceOnly() {
        val aliased = report(arrayOf(Aliased())).services
        assertEquals(listOf("Mac" to "TAG", "SecretKeyFactory" to "TAG-B"), aliased.map { it.type to it.algorithm })
        val factory = aliased.single { it.type == "SecretKeyFactory" }
        assertEquals(ServiceRequirement.PROBE_FAILED, factory.reason)
        assertEquals("IllegalStateException: no encoding", factory.detail)
    }

    @Test
    fun theDocumentRoundTrips() {
        val codec = YamlCodec()
        assertEquals(JVM, RequirementDocument.parse(codec.load(codec.dump(RequirementDocument.of(JVM)))))
    }

    @Test
    fun theFileWrittenOneServiceAtATimeIsTheDocument() {
        val folder = Files.createTempDirectory("requirements").toFile()
        val codec = YamlCodec()
        val file = RequirementYamlWriter(ProbeDirectory(folder)).write(JVM)
        assertEquals(codec.dump(RequirementDocument.of(JVM)), file.readText())
        folder.deleteRecursively()
    }

    @Suppress("DEPRECATION")
    private class Bound : Provider("Bound", 1.0, "keeps its keys inside") {
        init {
            put("Cipher.BOUND/CBC/NoPadding", RefusingCipher::class.java.name)
            put("KeyGenerator.BOUND", UnreadyGenerator::class.java.name)
        }
    }

    // TAG-B's own-name key is a password key whose encoding throws: describing it fails that alias's record only.
    @Suppress("DEPRECATION")
    private class Aliased : Provider("Aliased", 1.0, "a Mac with two aliases") {
        init {
            put("Mac.TAG", HmacTag::class.java.name)
            put("Alg.Alias.Mac.TAG-A", "TAG")
            put("Alg.Alias.Mac.TAG-B", "TAG")
            put("SecretKeyFactory.TAG-B", UnencodedFactory::class.java.name)
        }
    }

    class HmacTag : MacSpi() {
        private val inner = Mac.getInstance("HmacSHA256", "SunJCE")
        override fun engineGetMacLength() = inner.macLength
        override fun engineInit(key: Key, params: AlgorithmParameterSpec?) = inner.init(SecretKeySpec(key.encoded, "HmacSHA256"))
        override fun engineUpdate(input: Byte) = inner.update(input)
        override fun engineUpdate(input: ByteArray, offset: Int, len: Int) = inner.update(input, offset, len)
        override fun engineDoFinal(): ByteArray = inner.doFinal()
        override fun engineReset() = inner.reset()
    }

    class UnencodedFactory : SecretKeyFactorySpi() {
        override fun engineGenerateSecret(keySpec: KeySpec?): SecretKey = object : SecretKey {
            override fun getAlgorithm() = "TAG-B"
            override fun getFormat() = "RAW"
            override fun getEncoded(): ByteArray = throw IllegalStateException("no encoding")
        }
        override fun engineGetKeySpec(key: SecretKey?, keySpec: Class<*>?): KeySpec = throw UnsupportedOperationException()
        override fun engineTranslateKey(key: SecretKey?): SecretKey = throw UnsupportedOperationException()
    }

    @Suppress("DEPRECATION")
    private class Throwing : Provider("Throwing", 1.0, "a provider bug") {
        init {
            put("Cipher.THROWING/CBC/NoPadding", ThrowingCipher::class.java.name)
        }
    }

    open class RefusingCipher : CipherSpi() {
        open fun refusal(): Exception = InvalidKeyException("only keys born here")
        override fun engineSetMode(mode: String?) = Unit
        override fun engineSetPadding(padding: String?) = Unit
        override fun engineGetBlockSize() = 16
        override fun engineGetOutputSize(inputLen: Int) = inputLen
        override fun engineGetIV(): ByteArray? = null
        override fun engineGetParameters(): AlgorithmParameters? = null
        override fun engineInit(opmode: Int, key: Key?, random: SecureRandom?): Unit = throw refusal()
        override fun engineInit(opmode: Int, key: Key?, params: AlgorithmParameterSpec?, random: SecureRandom?): Unit = throw refusal()
        override fun engineInit(opmode: Int, key: Key?, params: AlgorithmParameters?, random: SecureRandom?): Unit = throw refusal()
        override fun engineUpdate(input: ByteArray?, inputOffset: Int, inputLen: Int): ByteArray? = null
        override fun engineUpdate(input: ByteArray?, inputOffset: Int, inputLen: Int, output: ByteArray?, outputOffset: Int) = 0
        override fun engineDoFinal(input: ByteArray?, inputOffset: Int, inputLen: Int): ByteArray? = null
        override fun engineDoFinal(input: ByteArray?, inputOffset: Int, inputLen: Int, output: ByteArray?, outputOffset: Int) = 0
    }

    class ThrowingCipher : RefusingCipher() {
        override fun refusal(): Exception = NullPointerException("modulus=" + "1234567890123456".repeat(40))
    }

    class UnreadyGenerator : KeyGeneratorSpi() {
        override fun engineInit(random: SecureRandom?) = Unit
        override fun engineInit(params: AlgorithmParameterSpec?, random: SecureRandom?) = Unit
        override fun engineInit(keysize: Int, random: SecureRandom?) = Unit
        override fun engineGenerateKey(): SecretKey = throw IllegalStateException("not initialized")
    }

    private companion object {
        val CAPTURE = ProviderProbe().capture(Security.getProviders())
        val JVM = RequirementTrial().run(
            CAPTURE,
            DefaultRunTrial().run(TrialRunner().run(CAPTURE, Security.getProviders()), Security.getProviders()),
            Security.getProviders(),
            DefaultKeys(Security.getProviders().toList()),
        )
    }
}
