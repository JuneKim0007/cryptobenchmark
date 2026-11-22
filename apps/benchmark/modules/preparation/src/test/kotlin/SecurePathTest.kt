package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.guide.Guide
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterialGenerator
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyPlanner
import io.github.junekim0007.cryptobench.preparation.key.secure.SecureKey
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.measurement.KeySource
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.measurement.Variant
import io.github.junekim0007.cryptobench.jca.bind.ParameterBinder
import io.github.junekim0007.cryptobench.preparation.prepare.CasePreparer
import io.github.junekim0007.cryptobench.preparation.prepare.PreparationException
import io.github.junekim0007.cryptobench.preparation.request.BenchmarkRequest
import io.github.junekim0007.cryptobench.preparation.request.Selection
import io.github.junekim0007.cryptobench.preparation.resolve.CaseResolver
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test
import java.security.ProviderException

/** The secure path on a JVM: refused with one coded line, the entry's other paths kept; its ids, backing tag and failure codes. */
class SecurePathTest {

    private val fixture = PreparationFixture()
    private val resolver = CaseResolver(fixture.device, ParameterBinder())
    private val keystore = mapOf("purposes" to listOf("ENCRYPT", "DECRYPT"))
    private fun aes(variants: List<Variant>?, keySource: KeySource = KeySource()) =
        Selection("KeyGenerator", "AES", "SunJCE", keySizes = listOf(128), variants = variants, keySource = keySource, keystore = keystore)
    private fun resolve(vararg selections: Selection, run: List<Variant> = listOf(Variant.FIXED)) =
        resolver.resolve(BenchmarkRequest(selections.toList(), EffectiveFixture.ONE_WARM_RUN.copy(variants = run)))

    @Test
    fun aSecurePathTheEntryWritesIsNotSupportedOnAJvmAndFixedStays() {
        val resolution = resolve(aes(listOf(Variant.FIXED, Variant.SECURE)))
        assertEquals(listOf("KeyGenerator_AES_GENERATE-KEY_SunJCE_k128_WARM_fixed"), resolution.cases.map { it.id })
        assertEquals(listOf("not_supported: secure needs android.security.keystore (AndroidKeyStore), absent on this runtime"), resolution.rejections.map { it.reason })
    }

    @Test
    fun theRunsSecurePathDropsQuietlyUnlessNothingIsLeft() {
        assertEquals(emptyList<String>(), resolve(aes(null), run = listOf(Variant.FIXED, Variant.SECURE)).rejections.map { it.reason })
        assertEquals(listOf("not_supported"), resolve(aes(null), run = listOf(Variant.SECURE)).rejections.map { it.reason.substringBefore(':') })
    }

    @Test
    fun aBackingWithoutASecureCaseIsUnused() =
        assertEquals(listOf("unused_setting: key.backing reaches no secure case"),
            resolve(aes(listOf(Variant.FIXED), KeySource(backing = "strongbox"))).rejections.map { it.reason })

    @Test
    fun aBackingIsTeeOrStrongbox() {
        val failure = assertThrows(IllegalArgumentException::class.java) { KeySource.split(mapOf("backing" to "glass"), "P.KeyGenerator.AES.key") }
        assertEquals("invalid: P.KeyGenerator.AES.key.backing glass, one of [tee, strongbox]", failure.message)
    }

    /** A secure id ends _secure; strongbox joins the p tag so tee and strongbox cases of one entry never collide; tee is the default. */
    @Test
    fun aSecureCaseIdEndsSecureAndStrongboxJoinsTheTag() {
        val case = BenchmarkCase("KeyGenerator", "AES", "AndroidKeyStore", Operation.GENERATE_KEY, keySize = 128, variant = Variant.SECURE)
        assertEquals("KeyGenerator_AES_GENERATE-KEY_AndroidKeyStore_k128_WARM_secure", case.id)
        assertEquals(case.id, case.copy(keySource = KeySource(backing = "tee")).id)
        assertEquals(true, Regex("_WARM_p[0-9a-f]{8}_secure$").containsMatchIn(case.copy(keySource = KeySource(backing = "strongbox")).id))
    }

    @Test
    fun theGuidesKeystoreBlockReachesTheSelection() {
        val guide = Guide(mapOf("AndroidKeyStore/KeyGenerator/AES" to mapOf("keystore" to keystore)))
        assertEquals(keystore, guide.joined(listOf(Selection("KeyGenerator", "AES", "AndroidKeyStore"))).first.single().keystore)
    }

    /** On a JVM a secure case that reaches preparation is the same not_supported line, never a reflection trace. */
    @Test
    fun aSecureCasePreparedOnAJvmIsNotSupported() {
        val binder = ParameterBinder()
        val preparer = CasePreparer(KeyPlanner(fixture.device), KeyMaterialGenerator(binder = binder), binder)
        val case = BenchmarkCase("KeyGenerator", "AES", "SunJCE", Operation.GENERATE_KEY, keySize = 128, variant = Variant.SECURE, keystore = keystore)
        val failure = assertThrows(PreparationException::class.java) { preparer.prepare(case) }
        assertEquals("not_supported: secure needs android.security.keystore (AndroidKeyStore), absent on this runtime", failure.reason)
    }

    @Test
    fun aRefusalIsStrongboxUnavailableOrKeystoreUnsupported() {
        val key = SecureKey(BenchmarkCase("KeyGenerator", "AES", "AndroidKeyStore", Operation.GENERATE_KEY, keySize = 192, variant = Variant.SECURE,
            keySource = KeySource(backing = "strongbox")))
        assertEquals("strongbox_unavailable: AndroidKeyStore strongbox: ProviderException: generate", key.refusal(ProviderException("generate", StrongBoxUnavailableException())))
        assertEquals("keystore_unsupported: KeyGenerator AES/192: IllegalArgumentException: size", key.refusal(ProviderException("x", IllegalArgumentException("size"))))
    }

    private class StrongBoxUnavailableException : ProviderException("no StrongBox")
}
