package io.github.junekim0007.cryptobench.discovery.trial.keystore

import io.github.junekim0007.cryptobench.discovery.contract.CapturedEnvironment
import io.github.junekim0007.cryptobench.discovery.contract.KeystoreRow
import io.github.junekim0007.cryptobench.discovery.contract.KeystoreSection
import io.github.junekim0007.cryptobench.discovery.contract.ProviderEntry
import io.github.junekim0007.cryptobench.discovery.contract.RequirementReport
import io.github.junekim0007.cryptobench.discovery.contract.RuntimeInfo
import io.github.junekim0007.cryptobench.discovery.contract.ServiceEntry
import io.github.junekim0007.cryptobench.discovery.contract.ServiceRequirement
import io.github.junekim0007.cryptobench.document.catalogue.FamilyCatalogue
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File
import java.security.InvalidAlgorithmParameterException
import java.security.KeyStoreException
import java.security.Provider

class KeystoreTrialTest {

    private class StrongBoxUnavailableException : RuntimeException("no StrongBox")

    private class FakeKeystore(private val strongBox: Boolean?, private val refuse: (KeystoreRequest) -> Throwable?) : KeystoreMaker {
        val generated = mutableListOf<String>()
        val deleted = mutableListOf<String>()
        val swept = mutableListOf<String>()
        override fun missing(): String? = null
        override fun strongBox(): Boolean? = strongBox
        override fun generate(provider: Provider, request: KeystoreRequest, alias: String, sdkInt: Int) {
            generated += alias
            refuse(request)?.let { throw it }
        }
        override fun sweep(provider: Provider, prefix: String) { swept += prefix }
        override fun delete(provider: Provider, alias: String) { deleted += alias }
    }

    private val keystore = object : Provider("Keystore", "1", "fake keystore") {}
    private val software = object : Provider("Software", "1", "fake software") {}

    private val capture = CapturedEnvironment(RuntimeInfo(sdkInt = 37), listOf(
        ProviderEntry("Keystore", 1, services = listOf(ServiceEntry("KeyPairGenerator", "RSA"), ServiceEntry("KeyPairGenerator", "ED25519"),
            ServiceEntry("KeyPairGenerator", "ML-DSA"), ServiceEntry("KeyGenerator", "AES"), ServiceEntry("KeyPairGenerator", "X", aliases = listOf("EC")))),
        ProviderEntry("Software", 2, services = listOf(ServiceEntry("KeyPairGenerator", "RSA"))),
    ), capturedAtMillis = 1L)

    private val requirements = RequirementReport(1L, 1L, listOf(
        born("KeyPairGenerator", "RSA"), born("KeyPairGenerator", "ED25519"), born("KeyPairGenerator", "ML-DSA"), born("KeyPairGenerator", "X"),
        ServiceRequirement("Keystore", "KeyGenerator", "AES", ServiceRequirement.NOT_RUNNABLE, reason = ServiceRequirement.KEY_REFUSED),
        ServiceRequirement("Software", "KeyPairGenerator", "RSA", ServiceRequirement.RUNNABLE),
    ))

    private val catalogue = KeystoreCatalogue(mapOf(
        ("KEYPAIRGENERATOR" to "RSA") to KeystoreCatalogue.Block(mapOf("purposes" to listOf("SIGN")), keySizes = listOf(2048, 4096)),
        ("KEYPAIRGENERATOR" to "ED25519") to KeystoreCatalogue.Block(mapOf("purposes" to listOf("SIGN"), "curve" to "ed25519")),
        ("KEYPAIRGENERATOR" to "EC") to KeystoreCatalogue.Block(mapOf("purposes" to listOf("SIGN")), curves = listOf("secp256r1")),
        ("KEYGENERATOR" to "AES") to KeystoreCatalogue.Block(mapOf("purposes" to listOf("ENCRYPT")), keySizes = listOf(128)),
    ))

    private fun born(type: String, algorithm: String) =
        ServiceRequirement("Keystore", type, algorithm, ServiceRequirement.NOT_RUNNABLE, reason = ServiceRequirement.KEYSTORE_BORN_KEY)

    private fun run(maker: KeystoreMaker): KeystoreSection = KeystoreTrial(maker) { catalogue }.run(capture, requirements, arrayOf(keystore, software))

    /** Each keystore-born generator with a block, by alias too: a row per size or curve and path, a fresh alias each, every alias deleted. */
    @Test
    fun recordsOneRowPerSizeAndPathWithCodedRefusals() {
        val maker = FakeKeystore(strongBox = true) { request ->
            when {
                request.backing == KeystoreRow.STRONGBOX && request.keySize == 4096 -> KeyStoreException("Unsupported key size")
                request.backing == KeystoreRow.STRONGBOX && request.algorithm == "ED25519" -> InvalidAlgorithmParameterException("outer", InvalidAlgorithmParameterException("Unsupported StrongBox EC: ed25519"))
                request.backing == KeystoreRow.STRONGBOX && request.curve == "secp256r1" -> RuntimeException("wrapped", StrongBoxUnavailableException())
                else -> null
            }
        }
        val rows = run(maker).rows
        assertEquals(listOf(
            "RSA tee 2048 ", "RSA tee 4096 ", "RSA strongbox 2048 ", "RSA strongbox 4096 keystore_unsupported: KeyPairGenerator RSA/4096 strongbox: KeyStoreException: Unsupported key size",
            "ED25519 tee null ", "ED25519 strongbox null keystore_unsupported: KeyPairGenerator ED25519 strongbox: InvalidAlgorithmParameterException: Unsupported StrongBox EC: ed25519",
            "X tee null secp256r1", "X strongbox null secp256r1strongbox_unavailable: Keystore strongbox: RuntimeException: wrapped",
        ), rows.map { "${it.algorithm} ${it.backing} ${it.keySize} ${it.curve}${it.error}" })
        assertEquals((0 until 8).map { "cryptobench-trial-$it" }, maker.generated)
        assertEquals(maker.generated, maker.deleted)
        assertEquals(listOf("cryptobench-trial-"), maker.swept)
    }

    @Test
    fun aDeviceWithoutStrongBoxRecordsItsRowsUntried() {
        val maker = FakeKeystore(strongBox = false) { null }
        val strongBox = run(maker).rows.filter { it.backing == KeystoreRow.STRONGBOX }
        assertEquals(4, strongBox.size)
        assertTrue(strongBox.all { !it.supported && it.error.startsWith("strongbox_unavailable: Keystore strongbox: the device declares no android.hardware.strongbox_keystore") })
        assertEquals(4, maker.generated.size)
    }

    @Test
    fun aMemberThisApiLacksIsApiTooLow() {
        val maker = FakeKeystore(strongBox = null) { KeystoreMaker.AbsentMember("api_too_low: PURPOSE_AGREE_KEY is absent on API 30") }
        assertTrue(run(maker).rows.all { it.error == "api_too_low: PURPOSE_AGREE_KEY is absent on API 30" })
    }

    /** A host JVM has no keystore classes: the section is absent with the reason, never an error. */
    @Test
    fun aRuntimeWithoutTheKeystoreClassesHasTheSectionAbsent() {
        val section = KeystoreTrial().run(capture, requirements, arrayOf(keystore))
        assertEquals(emptyList<KeystoreRow>(), section.rows)
        assertTrue(section.absent, section.absent.startsWith("not_supported: the keystore trial needs android.security.keystore"))
    }

    /** The bundled catalogues are the checkout's, and parse: authorizations without the trial lists, source or url. */
    @Test
    fun theBundledCatalogueBlocksParse() {
        val root = generateSequence(File("").absoluteFile) { it.parentFile }.first { File(it, "algorithms/setup-catalog.yaml").isFile }
        val files = KeystoreCatalogue.FAMILIES.map(FamilyCatalogue::file) + listOf(FamilyCatalogue.PROVIDER_BUILDS, FamilyCatalogue.DEVIATIONS)
        assertEquals(files.map { File(root, "algorithms/$it").readText() }, files.map(FamilyCatalogue::resource))
        val parsed = KeystoreCatalogue.bundled
        val rsa = parsed.of("KeyPairGenerator", listOf("rsa"))!!
        assertEquals(listOf(2048, 3072, 4096), rsa.keySizes)
        assertEquals(setOf("purposes", "digests", "encryptionPaddings", "signaturePaddings"), rsa.authorizations.keys)
        assertEquals(listOf("secp224r1", "secp256r1", "secp384r1", "secp521r1"), parsed.of("KeyPairGenerator", listOf("EC"))!!.curves)
        assertEquals("ed25519", parsed.of("KeyPairGenerator", listOf("ED25519"))!!.authorizations["curve"])
        assertEquals(listOf(128, 192, 256), parsed.of("KeyGenerator", listOf("AES"))!!.keySizes)
    }
}
