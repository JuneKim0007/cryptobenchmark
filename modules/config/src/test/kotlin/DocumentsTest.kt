package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.config.effective.EffectiveBuilder
import io.github.junekim0007.cryptobench.config.effective.EffectiveDocument
import io.github.junekim0007.cryptobench.config.global.GlobalDocument
import io.github.junekim0007.cryptobench.config.inventory.InventoryBuilder
import io.github.junekim0007.cryptobench.config.inventory.InventoryDocument
import io.github.junekim0007.cryptobench.config.source.CaptureSource
import io.github.junekim0007.cryptobench.config.source.TrialSource
import io.github.junekim0007.cryptobench.config.testset.TestSetDocument
import io.github.junekim0007.cryptobench.config.yaml.YamlFiles
import io.github.junekim0007.cryptobench.config.yaml.YamlCodec
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File
import java.nio.file.Files

/** Every handler round-trips through a real file, and the shared file layer stamps and checks the version. */
class DocumentsTest {

    private val files = YamlFiles()
    private val codec = YamlCodec()
    private val directory: File = Files.createTempDirectory("documents").toFile()
    private val inventory = InventoryBuilder().build(
        CaptureSource.parse(codec.load(Fixtures.CAPTURE)), TrialSource.parse(codec.load(Fixtures.TRIAL)), InventoryBuilder.Files("probe_x.yaml", "trial_x.yaml"))
    private val global = GlobalDocument.parse(codec.load(Fixtures.GLOBAL))
    private val testSet = TestSetDocument.parse(codec.load(Fixtures.TEST_SET))
    private val effective = EffectiveBuilder().build(global, testSet, inventory, EffectiveBuilder.Files("global.yaml", "testsets/scope.yaml", "inventory.yaml"))

    /** One override feeds many entries the same list; the file must still read back as plain values. */
    @Test
    fun everyKindRoundTripsInFull() {
        val warned = effective.copy(warnings = listOf("override_matches_nothing: {name=X}"))
        assertEquals(inventory, files.at(File(directory, "inventory.yaml"), InventoryDocument).let { it.write(inventory); it.read() })
        assertEquals(warned, files.at(File(directory, "effective.yaml"), EffectiveDocument).let { it.write(warned); it.read() })
        assertEquals(global, files.at(File(directory, "global.yaml"), GlobalDocument).let { it.write(global); it.read() })
        assertEquals(testSet, files.at(File(directory, "scope.yaml"), TestSetDocument).let { it.write(testSet); it.read() })
        val text = File(directory, "effective.yaml").readText()
        assertTrue(text, !text.contains("&id") && !text.contains("*id"))
    }

    @Test
    fun theFileLayerStampsAndChecksTheVersion() {
        val written = files.at(File(directory, "inventory.yaml"), InventoryDocument).write(inventory)
        assertTrue(written.readText().startsWith("schemaVersion: 1\n"))
        written.writeText(written.readText().replaceFirst("schemaVersion: 1", "schemaVersion: 9"))
        assertEquals("unsupported_schema_version: inventory.yaml: 9, this build reads 1",
            assertThrows(IllegalArgumentException::class.java) { files.at(written, InventoryDocument).read() }.message)
    }

    /** A misspelt section, key or choice fails by name instead of quietly falling back to defaults. */
    @Test
    fun malformedDocumentsAreRefusedByName() {
        val global = "schemaVersion: 1\nselection: {testSet: a.yaml}\n"
        listOf<Pair<() -> Any, String>>(
            { GlobalDocument.parse(codec.load(global + "rn: {}\n")) } to "unknown_section: [rn], known [selection, run, policy]",
            { GlobalDocument.parse(codec.load(global + "run: {inputSize: [1]}\n")) } to "unknown_keys: run [inputSize], known [inputSizes, phases, metrics, processRepetitions, seed]",
            { GlobalDocument.parse(codec.load(global + "policy: {onFailure: retry}\n")) } to "invalid: policy.onFailure retry, one of [stop, skip]",
            { GlobalDocument.parse(codec.load(global + "policy: {onUnavailable: skip}\n")) } to "unknown_keys: policy [onUnavailable], known [onFailure]",
            { GlobalDocument.parse(codec.load("schemaVersion: 1\nselection: {testSet: a.yaml, exclude: [{type: Mac}, {}]}\n")) } to "empty_rule: give provider, type or name at selection.exclude[1]",
            { TestSetDocument.parse(codec.load("schemaVersion: 1\noverrides:\n- {match: {type: Cipher}, set: {keySize: [1]}}\n")) } to "unknown_keys: overrides[0].set [keySize], known [keySizes, inputSizes, key, parameters, operations]",
            { codec.load("- one\n- two\n") } to "not_a_mapping: the document is not a set of key: value entries",
        ).forEach { (parse, expected) ->
            assertEquals(expected, assertThrows(IllegalArgumentException::class.java) { parse() }.message)
        }
        val duplicate = assertThrows(RuntimeException::class.java) { codec.load("schemaVersion: 1\nschemaVersion: 1\n") }.message!!
        assertTrue(duplicate, duplicate.contains("duplicate key"))
    }

    @Test
    fun aMissingRunSectionOrKeyKeepsDefaults() {
        val minimal = GlobalDocument.parse(codec.load("schemaVersion: 1\nselection: {testSet: testsets/all.yaml}\n"))
        assertEquals(listOf(1024), minimal.run.inputSizes)
        val partial = GlobalDocument.parse(codec.load("schemaVersion: 1\nselection: {testSet: testsets/all.yaml}\nrun: {processRepetitions: 3}\n"))
        assertEquals(3, partial.run.processRepetitions)
        assertEquals(listOf(1024), partial.run.inputSizes)
    }
}
