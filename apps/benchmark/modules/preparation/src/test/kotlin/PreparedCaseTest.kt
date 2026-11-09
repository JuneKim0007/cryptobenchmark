package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertSame
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

/** What a prepared case carries: its key, its input and its bound parameters, and that a misfit is caught before the run. */
class PreparedCaseTest {

    private val fixture = PreparationFixture()
    private val directory = fixture.directory
    private val preparation = fixture.preparation
    private fun effective(onFailure: String) = fixture.effective(onFailure)

    /** One key per recipe: every input size of AES-128 shares it, and nothing is generated twice. */
    @Test
    fun aKeyIsMadeOncePerRecipe() {
        val aes = preparation.prepareAll(effective("skip")).cases.filter { it.case.algorithm == "AES/GCM/NoPadding" }
        assertSame(aes[0].key, aes[1].key)
        assertTrue(aes[0].key is KeyMaterial.Secret)
    }

    /** fresh(12) must be drawn per call, so the harness is told the spec varies. */
    @Test
    fun boundParametersComeWithTheCase() {
        val gcm = preparation.prepareAll(effective("skip")).cases.first { it.case.algorithm == "AES/GCM/NoPadding" }
        assertNotNull(gcm.parameters)
        assertTrue(gcm.parameters!!.varies)
        assertEquals(null, preparation.prepareAll(effective("skip")).cases.first { it.case.algorithm == "SHA-256" }.parameters)
    }

    /** The one call before the run is also where the provider's parameters are read back. */
    @Test
    fun aPreparedCaseCarriesWhatTheProviderUsed() {
        val cases = preparation.prepareAll(effective("skip")).cases
        val gcm = cases.first { it.case.algorithm == "AES/GCM/NoPadding" }
        assertEquals(12, gcm.resolvedParameters["ivBytes"])
        assertEquals(128, gcm.resolvedParameters["tagBits"])
        assertEquals(gcm.case.keySize, gcm.resolvedParameters["keyBits"])
        assertEquals(emptyMap<String, Any>(), cases.first { it.case.algorithm == "SHA-256" }.resolvedParameters)
    }

    /** Encrypt is called once with the case's own key: a 256-bit key on AES_128 fails here, not inside the timed region. */
    @Test
    fun aKeyThatDoesNotFitTheAlgorithmIsCaughtBeforeTheRun() {
        val file = File(directory, "mismatch.yaml").apply {
            writeText(effective("skip").readText().replace("      ChaCha20: {}", "      AES_128/GCM/NoPadding: {keySizes: [256]}"))
        }.also { GuideFixture.beside(it) }
        val run = preparation.prepareAll(file)
        val mismatch = run.skipped.filter { it.name == "AES_128/GCM/NoPadding" }
        assertEquals(8, mismatch.size)
        assertTrue(mismatch.first().reason, mismatch.first().reason.contains("dry_run_failed: InvalidKeyException"))
        assertTrue(run.cases.none { it.case.algorithm == "AES_128/GCM/NoPadding" })
    }
}
