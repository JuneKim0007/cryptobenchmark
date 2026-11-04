package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.prepare.StoppedOnFailureException
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

/** What preparation does with a case it cannot build: skip or stop, and the report it leaves either way. */
class PreparationPolicyTest {

    private val fixture = PreparationFixture()
    private val directory = fixture.directory
    private val preparation = fixture.preparation
    private fun effective(onFailure: String) = fixture.effective(onFailure)

    @Test
    fun skipPreparesWhatItCanAndRecordsTheRest() {
        val run = preparation.prepare(effective("skip"))
        assertEquals(List(8) { "AES/GCM/NoPadding" } + List(4) { "SHA-256" }, run.cases.map { it.case.algorithm })
        assertEquals(listOf("fixed", "notFixed"), run.cases.map { it.case.variant.label }.distinct())
        assertEquals(List(4) { "SUN" }, run.cases.filter { it.case.algorithm == "SHA-256" }.map { it.case.provider })
        assertEquals(3, run.processRepetitions)
        val reasons = run.skipped.map { it.toString() }
        assertTrue(reasons.toString(), reasons.contains("[preparation] SunJCE Cipher ChaCha20: not_registered"))
        assertTrue(reasons.toString(), reasons.any { it.startsWith("[preparation] SunJCE Cipher Serpent/CBC/NoPadding: Cipher_Serpent-CBC-NoPadding_ENCRYPT_SunJCE_k128_i64_WARM_fixed: key_generation_failed:") })
        assertTrue(File(directory, "preparation/skipped.yaml").readText().contains("stage: preparation"))
    }

    @Test
    fun anEmptyReportIsStillWritten() {
        val clean = File(directory, "clean.yaml").apply {
            writeText(effective("stop").readText().replace(Regex("(?m)^      (Serpent/CBC/NoPadding|ChaCha20):.*\n"), ""))
        }
        val run = preparation.prepare(clean)
        assertEquals(emptyList<Any>(), run.skipped)
        assertTrue(File(directory, "preparation/skipped.yaml").readText().contains("skipped: []"))
    }

    /** STOP still writes the report first, so the reason for stopping is on disk. */
    @Test
    fun stopListsEveryFailureAndStillWritesTheReport() {
        val error = assertThrows(StoppedOnFailureException::class.java) { preparation.prepare(effective("stop")) }
        assertEquals(9, error.skipped.size)
        assertTrue(File(directory, "preparation/skipped.yaml").exists())
    }
}
