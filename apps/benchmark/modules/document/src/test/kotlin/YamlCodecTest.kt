package io.github.junekim0007.cryptobench.document

import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test
import org.yaml.snakeyaml.composer.ComposerException

class YamlCodecTest {

    private val document = linkedMapOf(
        "name" to "SunJCE",
        "version" to "25",
        "services" to listOf(linkedMapOf("type" to "Cipher", "aliases" to listOf("a", "b"))),
    )

    @Test
    fun dumpsBlockStyleQuotesNumberLikeStringsAndLoadsItBack() {
        val text = YamlCodec.CAPTURE.dump(document)
        assertTrue(text, text.contains("version: '25'"))
        assertEquals(document, YamlCodec.CAPTURE.load(text))
    }

    @Test
    fun documentDumpsFlowStyleForLeafCollections() {
        assertEquals("name: SunJCE\nversion: '25'\nservices:\n- type: Cipher\n  aliases: [a, b]\n", YamlCodec.DOCUMENT.dump(document))
    }

    @Test
    fun documentRefusesAnEmptyDocumentAndAList() {
        listOf("", "- a\n- b\n").forEach { text ->
            val failure = assertThrows(IllegalArgumentException::class.java) { YamlCodec.DOCUMENT.load(text) }
            assertEquals("not_a_mapping: the document is not a set of key: value entries", failure.message)
        }
    }

    @Test
    fun currentBehaviourCaptureFailsUncodedOnAnEmptyDocumentAndAList() {
        val empty = assertThrows(NullPointerException::class.java) { YamlCodec.CAPTURE.load("") }
        assertEquals("null cannot be cast to non-null type kotlin.collections.Map<kotlin.String, kotlin.Any>", empty.message)
        val list = assertThrows(ClassCastException::class.java) { YamlCodec.CAPTURE.load("- a\n- b\n") }
        assertTrue(list.message, list.message!!.startsWith("class java.util.ArrayList cannot be cast to class java.util.Map"))
    }

    @Test
    fun captureRefusesAGlobalTag() {
        val failure = assertThrows(ComposerException::class.java) { YamlCodec.CAPTURE.load("!!java.util.Date {}\n") }
        assertTrue(failure.message, failure.message!!.startsWith("Global tag is not allowed: tag:yaml.org,2002:java.util.Date"))
    }

    /** A host requirements file is above SnakeYAML's 3 MiB default: every profile reads it. */
    @Test
    fun everyProfileLoadsADocumentAboveThreeMebibytes() {
        val text = sized(4 * MIB)
        YamlCodec.values().forEach { assertEquals(it.name, text.length / LINE.length, (it.load(text)["k"] as List<*>).size) }
    }

    /** A load is bounded by its own input, not a fixed limit. */
    @Test
    fun everyProfileLoadsADocumentPastSixteenMebibytes() {
        val text = sized(17 * MIB)
        YamlCodec.values().forEach { assertEquals(it.name, text.length / LINE.length, (it.load(text)["k"] as List<*>).size) }
    }

    // many short lines: one long scalar makes SnakeYAML's scan quadratic
    private fun sized(codePoints: Int): String = "k:\n" + LINE.repeat((codePoints - 3) / LINE.length + 1)

    private companion object {
        const val MIB = 1024 * 1024
        val LINE = "- " + "a".repeat(61) + "\n"
    }
}
