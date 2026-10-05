package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.input.OperationInput
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
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
        val aes = preparation.prepare(effective("skip")).cases.filter { it.case.algorithm == "AES/GCM/NoPadding" }
        assertSame(aes[0].key, aes[1].key)
        assertTrue(aes[0].key is KeyMaterial.Secret)
    }

    /** Every prepared case carries what its operation needs: decrypt its ciphertext, digest its message. */
    @Test
    fun eachCaseCarriesTheInputItsOperationNeeds() {
        val cases = preparation.prepare(effective("skip")).cases
        assertTrue(cases.filter { it.case.operation == Operation.DECRYPT }.all { it.input is OperationInput.Ciphertext })
        assertTrue(cases.filter { it.case.algorithm == "SHA-256" }.all { it.input is OperationInput.Message })
    }

    /** fresh(12) must be drawn per call, so the harness is told the spec varies. */
    @Test
    fun boundParametersComeWithTheCase() {
        val gcm = preparation.prepare(effective("skip")).cases.first { it.case.algorithm == "AES/GCM/NoPadding" }
        assertNotNull(gcm.parameters)
        assertTrue(gcm.parameters!!.varies)
        assertEquals(null, preparation.prepare(effective("skip")).cases.first { it.case.algorithm == "SHA-256" }.parameters)
    }

    /** Encrypt is called once with the case's own key: a 256-bit key on AES_128 fails here, not inside the timed region. */
    @Test
    fun aKeyThatDoesNotFitTheAlgorithmIsCaughtBeforeTheRun() {
        val file = File(directory, "mismatch.yaml").apply {
            writeText(effective("skip").readText().replace("      ChaCha20: {}", "      AES_128/GCM/NoPadding: {keySizes: [256]}"))
        }
        val run = preparation.prepare(file)
        val mismatch = run.skipped.filter { it.name == "AES_128/GCM/NoPadding" }
        assertEquals(4, mismatch.size)
        assertTrue(mismatch.first().reason, mismatch.first().reason.contains("dry_run_failed: InvalidKeyException"))
        assertTrue(run.cases.none { it.case.algorithm == "AES_128/GCM/NoPadding" })
    }
}
