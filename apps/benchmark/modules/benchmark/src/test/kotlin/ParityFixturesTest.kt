package io.github.junekim0007.cryptobench.benchmark

import io.github.junekim0007.cryptobench.benchmark.report.CaseDocument
import io.github.junekim0007.cryptobench.benchmark.report.jetpack.JetpackResults
import io.github.junekim0007.cryptobench.benchmark.verify.known.KnownAnswerFile
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFile
import org.junit.Assert.assertEquals
import org.junit.Test
import org.yaml.snakeyaml.LoaderOptions
import org.yaml.snakeyaml.Yaml
import org.yaml.snakeyaml.constructor.SafeConstructor
import java.io.File

/** parity/: the known answers Python writes, and the thermal.json apps/benchmark-runner/tests/test_thermal_document.py pins byte for byte, as this module reads them. */
class ParityFixturesTest {

    private val parity = generateSequence(File("").absoluteFile) { it.parentFile }.map { File(it, "parity") }.first { File(it, "duplicate-key.yaml").isFile }

    private fun stated(name: String): Map<String, Any> = Yaml(SafeConstructor(LoaderOptions())).load(File(parity, "$name.json").readText())

    @Test
    fun theKnownAnswersPythonWroteReadToTheirStatedValueAndVectors() {
        assertEquals(stated("known-answers"), DocumentFile.read(File(parity, "known-answers.yaml"), "known_answers", 1))
        val vectors = KnownAnswerFile.read(File(parity, "known-answers.yaml"))
        assertEquals(listOf("sha256-abc", "hmac-sha256-rfc4231-case2", "aes128-gcm-cavp-encryptextiv-pt256-count0", "aes128-kw-rfc3394-4.1"), vectors.map { it.id })
        assertEquals(listOf("AESWrap", "AES/KW/NoPadding"), vectors.last().algorithms)
    }

    @Test
    fun theThermalFilePythonWritesReachesTheCaseRow() {
        val text = File(parity, "thermal.json").readText()
        val readings = JetpackResults.thermalOf(text)
        assertEquals(setOf("a", "b"), readings.keys)
        assertEquals(mapOf("start" to null, "end" to mapOf("skin" to 33.1), "startStatus" to null, "endStatus" to 0,
            "note" to "thermal_unavailable: fake", "gate" to mapOf("waitedSeconds" to 240.0, "target" to 35.75, "discards" to 0)), readings.getValue("a"))
        val example = File("example")
        val data = File(example, "benchmark_jetpack_example.json").readText()
        val prepared = File(example, "benchmark_prepared_example.yaml").readText()
        val digestId = JetpackResults.convert(data, prepared).rows.single { it.algorithm == "SHA-256" }.id
        val digest = JetpackResults.convert(data, prepared, thermal = JetpackResults.thermalOf(text.replace("\"a\"", "\"$digestId\"")))
            .rows.single { it.id == digestId }
        assertEquals(mapOf("start" to null, "end" to mapOf("skin" to 33.1), "startStatus" to null, "endStatus" to 0), digest.thermal)
        assertEquals("thermal_unavailable: fake", digest.thermalNote)
        assertEquals(mapOf("waitedSeconds" to 240.0, "target" to 35.75, "discards" to 0), digest.gate)
    }

    @Test
    fun currentBehaviourADuplicateKeyKeepsTheLastValueInCaseDocument() {
        assertEquals(mapOf("schemaVersion" to 1, "run" to mapOf("seed" to 2), "seed" to "last"), CaseDocument.load(File(parity, "duplicate-key.yaml").readText()))
    }
}
