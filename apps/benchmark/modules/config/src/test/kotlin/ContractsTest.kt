package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.config.effective.EffectiveDocument
import io.github.junekim0007.cryptobench.config.global.GlobalDocument
import io.github.junekim0007.cryptobench.config.names.AlgorithmNames
import io.github.junekim0007.cryptobench.config.names.dto.Canonical
import io.github.junekim0007.cryptobench.document.YamlCodec
import io.github.junekim0007.cryptobench.files.RepositoryFiles
import io.github.junekim0007.cryptobench.config.yaml.YamlFiles
import io.github.junekim0007.cryptobench.settings.Facts
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Assume
import org.junit.Test
import org.yaml.snakeyaml.LoaderOptions
import org.yaml.snakeyaml.Yaml
import org.yaml.snakeyaml.constructor.DuplicateKeyException
import org.yaml.snakeyaml.constructor.SafeConstructor
import java.io.File

/** tests/contracts/: each shared YAML (config's examples, the facts fixture, the codec cases) reads through :config's codec to the value its .json holds, as apps/benchmark-runner/tests/test_contracts.py reads it. */
class ContractsTest {

    private val codec = YamlCodec.DOCUMENT

    private val global = RepositoryFiles.example("config", "config_global_example.yaml")
    private val effective = RepositoryFiles.example("config", "config_effective_example.yaml")

    private fun stated(folder: File, name: String): Map<String, Any> = Yaml(SafeConstructor(LoaderOptions())).load(File(folder, "$name.json").readText())

    private fun read(folder: File, name: String): Map<String, Any> = read(File(folder, "$name.yaml"))

    private fun read(file: File): Map<String, Any> = codec.load(file.readText())

    @Test
    fun eachFixtureReadsToItsStatedValue() {
        plainRun()
        for (file in listOf(global, effective, File(RepositoryFiles.documents, "facts.yaml"))) {
            assertEquals(file.name, stated(RepositoryFiles.documents, file.nameWithoutExtension), read(file))
        }
        assertEquals(stated(RepositoryFiles.yamlCodec, "scalars"), read(RepositoryFiles.yamlCodec, "scalars") - "exponentNoDot")
    }

    @Test
    fun currentBehaviourAnUnquotedExponentWithoutADotIsADouble() {
        // Python reads the same plain 1e3 as the string "1e3"
        assertEquals(1000.0, read(RepositoryFiles.yamlCodec, "scalars")["exponentNoDot"])
    }

    @Test
    fun currentBehaviourAnExponentLikeStringPythonWroteReadsAsADouble() {
        @Suppress("UNCHECKED_CAST")
        val strings = read(RepositoryFiles.yamlCodec, "python-strings")["strings"] as Map<String, Any>
        @Suppress("UNCHECKED_CAST")
        val written = stated(RepositoryFiles.yamlCodec, "python-strings")["strings"] as Map<String, Any>
        assertEquals(mapOf("exponent" to 1000.0, "exponentLong" to 1.2E46), strings.filter { it.value != written[it.key] })
    }

    @Test
    fun currentBehaviourADuplicateKeyIsRefused() {
        assertThrows(DuplicateKeyException::class.java) { read(RepositoryFiles.yamlCodec, "duplicate-key") }
    }

    @Test
    fun theAuthoredAndGeneratedFixturesPassTheirReaders() {
        plainRun()
        val files = YamlFiles()
        files.at(global, GlobalDocument).read()
        files.at(effective, EffectiveDocument).read()
        assertEquals(effective.readText(), codec.dump(read(effective)))
    }

    @Test
    fun theFactsPythonWroteAreTheFactsKotlinReads() {
        val facts = Facts.read(read(RepositoryFiles.documents, "facts"))
        assertEquals(Facts(true, 37, listOf(Facts.Core(0, true, 2246000), Facts.Core(1, false, null), Facts.Core(7, true, 3782000)), true), facts)
    }

    @Test
    fun theNamesFileResolvesAsPythonResolvesIt() {
        val names = AlgorithmNames.catalog
        assertEquals(Canonical("SHA-1"), names.canonical("MessageDigest", "sha"))
        assertEquals(Canonical("DESede"), names.canonical("Cipher", "tripledes"))
        assertEquals(Canonical("AES", 256), names.canonical("Cipher", "AES_256"))
        assertEquals(Canonical("NotAnAlgorithm", null, false), names.canonical("Cipher", "NotAnAlgorithm"))
    }

    // an update run writes the examples and their .json; only a plain run checks them
    private fun plainRun() = Assume.assumeTrue(System.getProperty("examples.update") == null)
}
