package io.github.junekim0007.cryptobench.preparation

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

/** What preparation does with a case it cannot build: list it, then throw with the step's code, which the orchestrator records as a skip. */
class PreparationPolicyTest {

    private val fixture = PreparationFixture()
    private val directory = fixture.directory
    private val preparation = fixture.preparation
    private fun effective(onFailure: String) = fixture.effective(onFailure)

    @Test
    fun skipPreparesWhatItCanAndRecordsTheRest() {
        val run = preparation.prepareAll(effective("skip"), File(directory, "preparation"))
        assertEquals(List(8) { "AES/GCM/NoPadding" } + List(4) { "SHA-256" }, run.cases.map { it.case.algorithm })
        assertEquals(listOf("fixed", "notFixed"), run.cases.map { it.case.variant.label }.distinct())
        assertEquals(List(4) { "SUN" }, run.cases.filter { it.case.algorithm == "SHA-256" }.map { it.case.provider })
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
        val run = preparation.prepareAll(clean, File(directory, "preparation"))
        assertEquals(emptyList<Any>(), run.skipped)
        assertTrue(File(directory, "preparation/skipped.yaml").readText().contains("skipped: []"))
    }
}
