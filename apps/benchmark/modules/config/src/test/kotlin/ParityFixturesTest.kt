package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.config.effective.EffectiveDocument
import io.github.junekim0007.cryptobench.config.global.GlobalDocument
import io.github.junekim0007.cryptobench.config.names.AlgorithmNames
import io.github.junekim0007.cryptobench.config.names.dto.Canonical
import io.github.junekim0007.cryptobench.config.yaml.YamlCodec
import io.github.junekim0007.cryptobench.config.yaml.YamlFiles
import io.github.junekim0007.cryptobench.settings.Facts
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test
import org.yaml.snakeyaml.LoaderOptions
import org.yaml.snakeyaml.Yaml
import org.yaml.snakeyaml.constructor.DuplicateKeyException
import org.yaml.snakeyaml.constructor.SafeConstructor
import java.io.File

/** parity/: each shared YAML reads through :config's codec to the value its .json holds, as apps/benchmark-runner/tests/test_parity_fixtures.py reads it. */
class ParityFixturesTest {

    private val parity = generateSequence(File("").absoluteFile) { it.parentFile }.map { File(it, "parity") }.first { File(it, "duplicate-key.yaml").isFile }
    private val codec = YamlCodec()

    private fun stated(name: String): Map<String, Any> = Yaml(SafeConstructor(LoaderOptions())).load(File(parity, "$name.json").readText())

    private fun read(name: String): Map<String, Any> = codec.load(File(parity, "$name.yaml").readText())

    @Test
    fun eachFixtureReadsToItsStatedValue() {
        for (name in listOf("global", "effective", "facts", "algorithm-names")) {
            assertEquals(name, stated(name), read(name))
        }
        assertEquals(stated("scalars"), read("scalars") - "exponentNoDot")
    }

    @Test
    fun currentBehaviourAnUnquotedExponentWithoutADotIsADouble() {
        // Python reads the same plain 1e3 as the string "1e3"
        assertEquals(1000.0, read("scalars")["exponentNoDot"])
    }

    @Test
    fun currentBehaviourAnExponentLikeStringPythonWroteReadsAsADouble() {
        @Suppress("UNCHECKED_CAST")
        val strings = read("python-strings")["strings"] as Map<String, Any>
        @Suppress("UNCHECKED_CAST")
        val written = stated("python-strings")["strings"] as Map<String, Any>
        assertEquals(mapOf("exponent" to 1000.0, "exponentLong" to 1.2E46), strings.filter { it.value != written[it.key] })
    }

    @Test
    fun currentBehaviourADuplicateKeyIsRefused() {
        assertThrows(DuplicateKeyException::class.java) { read("duplicate-key") }
    }

    @Test
    fun theAuthoredAndGeneratedFixturesPassTheirReaders() {
        val files = YamlFiles()
        files.at(File(parity, "global.yaml"), GlobalDocument).read()
        files.at(File(parity, "effective.yaml"), EffectiveDocument).read()
        assertEquals(File(parity, "effective.yaml").readText(), codec.dump(read("effective")))
    }

    @Test
    fun theFactsPythonWroteAreTheFactsKotlinReads() {
        val facts = Facts.read(read("facts"))
        assertEquals(Facts(true, 37, listOf(Facts.Core(0, true, 2246000), Facts.Core(1, false, null), Facts.Core(7, true, 3782000)), true), facts)
    }

    @Test
    fun theNamesFixtureResolvesAsPythonResolvesIt() {
        val names = AlgorithmNames.parse(read("algorithm-names"))
        assertEquals(Canonical("SHA-1"), names.canonical("MessageDigest", "sha"))
        assertEquals(Canonical("DESede"), names.canonical("Cipher", "tripledes"))
        assertEquals(Canonical("AES", 256), names.canonical("Cipher", "AES_256"))
        assertEquals(Canonical("ChaCha20", null, false), names.canonical("Cipher", "ChaCha20"))
    }
}
