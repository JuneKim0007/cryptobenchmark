package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.port.Availability
import io.github.junekim0007.cryptobench.preparation.port.DeviceCapability
import io.github.junekim0007.cryptobench.preparation.prepare.StoppedOnFailureException
import io.github.junekim0007.cryptobench.preparation.report.SkipFile
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertSame
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File
import java.nio.file.Files

class PreparationTest {

    private val directory: File = Files.createTempDirectory("preparation").toFile()

    /** SunJCE really generates AES; "Serpent" is claimed by this device but no provider on the JVM can make its key. */
    private val device = object : DeviceCapability {
        private val serves = setOf("Cipher/AES/GCM/NoPadding", "KeyGenerator/AES", "Cipher/Serpent/CBC/NoPadding", "KeyGenerator/Serpent", "MessageDigest/SHA-256")
        override fun providers(): List<String> = listOf("SunJCE")
        override fun check(provider: String, type: String, algorithm: String): Availability =
            if (provider == "SunJCE" && "$type/$algorithm" in serves) Availability.Available else Availability.Unavailable("not_registered")
    }

    private fun effective(onFailure: String) = File(directory, "effective.yaml").apply {
        writeText("""
schemaVersion: 1
generatedFrom: {global: g, testSet: t, inventory: i, capture: c, trial: t, device: {}}
run: {inputSizes: [64, 1024], phases: [WARM], metrics: [TIME], processRepetitions: 3, seed: 0}
policy: {onFailure: $onFailure}
providers:
  SunJCE:
    Cipher:
      AES/GCM/NoPadding:
        keySizes: [128]
        parameters: {class: javax.crypto.spec.GCMParameterSpec, arguments: [128, fresh(12)]}
      Serpent/CBC/NoPadding: {keySizes: [128]}
      ChaCha20: {}
    MessageDigest:
      SHA-256: {}
skipped: []
""".trimIndent())
    }

    private val preparation = Preparation(device, SkipFile(File(directory, "preparation")))

    @Test
    fun skipPreparesWhatItCanAndRecordsTheRest() {
        val run = preparation.prepare(effective("skip"))
        assertEquals(listOf("AES/GCM/NoPadding", "AES/GCM/NoPadding", "AES/GCM/NoPadding", "AES/GCM/NoPadding", "SHA-256", "SHA-256"), run.cases.map { it.case.algorithm })
        assertEquals(3, run.processRepetitions)
        val reasons = run.skipped.map { it.toString() }
        assertTrue(reasons.toString(), reasons.contains("[preparation] SunJCE Cipher ChaCha20: not_registered"))
        assertTrue(reasons.toString(), reasons.any { it.startsWith("[preparation] SunJCE Cipher Serpent/CBC/NoPadding: Cipher_Serpent-CBC-NoPadding_ENCRYPT_SunJCE_k128_i64_WARM: key_generation_failed:") })
        assertTrue(File(directory, "preparation/skipped.yaml").readText().contains("stage: preparation"))
    }

    /** One key per recipe: every input size of AES-128 shares it, and nothing is generated twice. */
    @Test
    fun aKeyIsMadeOncePerRecipe() {
        val aes = preparation.prepare(effective("skip")).cases.filter { it.case.algorithm == "AES/GCM/NoPadding" }
        assertSame(aes[0].key, aes[1].key)
        assertTrue(aes[0].key is KeyMaterial.Secret)
    }

    /** fresh(12) must be drawn per call, so the harness is told the spec varies. */
    @Test
    fun boundParametersComeWithTheCase() {
        val gcm = preparation.prepare(effective("skip")).cases.first { it.case.algorithm == "AES/GCM/NoPadding" }
        assertNotNull(gcm.parameters)
        assertTrue(gcm.parameters!!.varies)
        assertEquals(null, preparation.prepare(effective("skip")).cases.first { it.case.algorithm == "SHA-256" }.parameters)
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
        assertEquals(5, error.skipped.size)
        assertTrue(File(directory, "preparation/skipped.yaml").exists())
    }
}
