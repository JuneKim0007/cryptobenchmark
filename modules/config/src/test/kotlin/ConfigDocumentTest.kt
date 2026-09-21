package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.config.generate.DefaultConfigBuilder
import io.github.junekim0007.cryptobench.config.source.CaptureSource
import io.github.junekim0007.cryptobench.config.source.TrialSource
import io.github.junekim0007.cryptobench.config.write.ConfigDocument
import io.github.junekim0007.cryptobench.config.write.YamlCodec
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test

class ConfigDocumentTest {

    private val codec = YamlCodec()
    private val config = DefaultConfigBuilder().build(
        CaptureSource.read("probe_x.yaml", codec.load(Fixtures.CAPTURE)),
        TrialSource.read("trial_x.yaml", codec.load(Fixtures.TRIAL)),
    )

    private fun rejection(text: String): String? =
        assertThrows(RuntimeException::class.java) { ConfigDocument.parse(codec.load(text)) }.message

    @Test
    fun roundTripsThroughYaml() {
        assertEquals(config, ConfigDocument.parse(codec.load(codec.dump(ConfigDocument.of(config)))))
    }

    /** What a user edits: switch an entry off, change its sizes. */
    @Test
    fun readsAHandEditedFile() {
        val text = codec.dump(ConfigDocument.of(config))
            .replace("AES/CBC/PKCS5PADDING:\n        enabled: true\n        keySizes: [256]", "AES/CBC/PKCS5PADDING:\n        enabled: false\n        keySizes: [128, 256]")
        val entry = ConfigDocument.parse(codec.load(text)).providers.getValue("SunJCE").getValue("Cipher").getValue("AES/CBC/PKCS5PADDING")
        assertEquals(false, entry.enabled)
        assertEquals(listOf(128, 256), entry.keySizes)
    }

    /** Key and parameter trees pass through untouched; config does not interpret them. */
    @Test
    fun keyAndParameterTreesPassThrough() {
        val text = codec.dump(ConfigDocument.of(config)).replace(
            "AES/CBC/PKCS5PADDING:\n        enabled: true\n",
            "AES/CBC/PKCS5PADDING:\n        enabled: true\n        parameters: {class: javax.crypto.spec.IvParameterSpec, arguments: [fresh(16)]}\n",
        )
        val parsed = ConfigDocument.parse(codec.load(text))
        val entry = parsed.providers.getValue("SunJCE").getValue("Cipher").getValue("AES/CBC/PKCS5PADDING")
        assertEquals(mapOf("class" to "javax.crypto.spec.IvParameterSpec", "arguments" to listOf("fresh(16)")), entry.parameters)
        assertEquals(parsed, ConfigDocument.parse(codec.load(codec.dump(ConfigDocument.of(parsed)))))
    }

    @Test
    fun aNameWrittenTwiceInDifferentCaseIsRejected() {
        val text = codec.dump(ConfigDocument.of(config)).replace("      RSA:\n", "      aes/cbc/pkcs5padding:\n")
        assertTrue(rejection(text)!!.startsWith("duplicate_name: SunJCE.Cipher"))
    }

    /** snakeyaml would otherwise keep the last one and drop the first without a word. */
    @Test
    fun aKeyWrittenTwiceIsRejected() {
        val text = "schemaVersion: 1\nschemaVersion: 1\n"
        assertTrue(assertThrows(RuntimeException::class.java) { codec.load(text) }.message!!.contains("duplicate key"))
    }

    @Test
    fun namesTheBrokenField() {
        assertEquals("missing_field: run", rejection("schemaVersion: 1\ngeneratedFrom: {capture: a, trial: b, device: {}}\nproviders: {}\n"))
        assertEquals("unsupported_schema_version: 9, this build reads 1", rejection("schemaVersion: 9\n"))
        assertEquals("wrong_type: SunJCE.Cipher.AES", rejection(
            "schemaVersion: 1\ngeneratedFrom: {capture: a, trial: b, device: {}}\n" +
                "run: {inputSizes: [1024], phases: [WARM], metrics: [TIME], processRepetitions: 1, seed: 0}\n" +
                "providers: {SunJCE: {Cipher: {AES: yes}}}\n"))
    }
}
