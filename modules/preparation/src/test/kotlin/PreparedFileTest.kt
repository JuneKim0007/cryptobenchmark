package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.adapter.DiscoveryCapability
import io.github.junekim0007.cryptobench.preparation.record.PreparedFile
import io.github.junekim0007.cryptobench.preparation.report.SkipFile
import io.github.junekim0007.cryptobench.preparation.shared.YamlCodec
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
import java.io.File

/**
 * The record is written from the cases that were built, so it cannot describe a run that did not
 * happen: a key generated at the provider's default size shows up here as the wrong encoded length.
 */
class PreparedFileTest {

    @get:Rule
    val output = TemporaryFolder()

    private val example = File("example")

    private fun prepare(effectiveText: String? = null): Map<String, Any> {
        val directory = output.newFolder()
        val effective = if (effectiveText == null) File(example, "preparation_effective_example.yaml") else
            File(directory, "effective.yaml").apply { writeText(effectiveText) }
        val record = PreparedFile(directory)
        Preparation(
            DiscoveryCapability(File(example, "preparation_capture_example.yaml"), File(example, "preparation_trial_example.yaml")),
            SkipFile(directory),
            record,
        ).prepare(effective)
        return YamlCodec().load(record.file.readText())
    }

    @Suppress("UNCHECKED_CAST")
    private fun cases(document: Map<String, Any>) = document["cases"] as List<Map<String, Any>>

    /** Keys are generated fresh on every run; only their shape is recorded, so the file is stable. */
    @Test
    fun theSameEffectiveFileRecordsTheSameRunTwice() {
        assertEquals(prepare(), prepare())
    }

    @Test
    fun aRecordedKeyIsTheKeyThatWasBuilt() {
        cases(prepare()).forEach { case ->
            @Suppress("UNCHECKED_CAST") val key = case["key"] as Map<String, Any>
            if (key["kind"] == "secret" && key["algorithm"] == "AES") {
                assertEquals(case["id"].toString(), case["keySize"], (key["encodedBytes"] as Int) * 8)
            }
        }
    }

    @Test
    fun aRecordedInputIsTheInputThatWasBuilt() {
        cases(prepare()).forEach { case ->
            @Suppress("UNCHECKED_CAST") val input = case["input"] as Map<String, Any>
            when (input["kind"]) {
                "message" -> assertEquals(case["id"].toString(), case["inputSize"], input["bytes"])
                "ciphertext" -> assertTrue(case["id"].toString(), (input["bytes"] as Int) >= (input["plaintextBytes"] as Int))
            }
        }
    }

    /** A harness setting is part of what a case is: two runs that time differently are not the same case. */
    @Test
    fun aFingerprintFollowsWhatTheCaseSays() {
        val text = File(example, "preparation_effective_example.yaml").readText()
        val fewer = text.replace("      SHA-256: {}", "      SHA-256: {harness: {iterations: 5}}")
        val digest = { document: Map<String, Any> -> cases(document).single { it["algorithm"] == "SHA-256" } }
        assertNotEquals(digest(prepare())["fingerprint"], digest(prepare(fewer))["fingerprint"])
        assertEquals(mapOf("iterations" to 5), digest(prepare(fewer))["harness"])
    }
}
