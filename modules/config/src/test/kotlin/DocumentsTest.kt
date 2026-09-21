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
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File
import java.nio.file.Files

/** Every handler round-trips through a real file, and the shared file layer stamps and checks the version. */
class DocumentsTest {

    private val files = YamlFiles()
    private val directory: File = Files.createTempDirectory("documents").toFile()
    private val inventory = InventoryBuilder().build(
        CaptureSource.parse(files.load(Fixtures.CAPTURE)), TrialSource.parse(files.load(Fixtures.TRIAL)), InventoryBuilder.Files("probe_x.yaml", "trial_x.yaml"))
    private val global = GlobalDocument.parse(files.load(Fixtures.GLOBAL))
    private val testSet = TestSetDocument.parse(files.load(Fixtures.TEST_SET))
    private val effective = EffectiveBuilder().build(global, testSet, inventory, EffectiveBuilder.Files("global.yaml", "testsets/scope.yaml", "inventory.yaml"))

    @Test
    fun everyKindRoundTrips() {
        assertEquals(inventory, files.at(File(directory, "inventory.yaml"), InventoryDocument).let { it.write(inventory); it.read() })
        assertEquals(effective, files.at(File(directory, "effective.yaml"), EffectiveDocument).let { it.write(effective); it.read() })
        assertEquals(global, files.at(File(directory, "global.yaml"), GlobalDocument).let { it.write(global); it.read() })
        assertEquals(testSet, files.at(File(directory, "scope.yaml"), TestSetDocument).let { it.write(testSet); it.read() })
    }

    /** One override feeds many entries the same list; the file must still read as plain values. */
    @Test
    fun sharedValuesAreWrittenInFull() {
        val text = files.at(File(directory, "effective.yaml"), EffectiveDocument).write(effective).readText()
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

    /** A misspelt section or key fails instead of quietly falling back to defaults. */
    @Test
    fun unknownSectionsAndKeysAreRefused() {
        assertEquals("unknown_section: [rn], known [selection, run, policy]",
            assertThrows(IllegalArgumentException::class.java) { GlobalDocument.parse(files.load("schemaVersion: 1\nselection: {testSet: a.yaml}\nrn: {}\n")) }.message)
        assertEquals("unknown_keys: run [inputSize], known [inputSizes, phases, metrics, processRepetitions, seed]",
            assertThrows(IllegalArgumentException::class.java) { GlobalDocument.parse(files.load("schemaVersion: 1\nselection: {testSet: a.yaml}\nrun: {inputSize: [1]}\n")) }.message)
        assertEquals("unknown_keys: overrides[0].set [keySize], known [keySizes, inputSizes, key, parameters, operations]",
            assertThrows(IllegalArgumentException::class.java) { TestSetDocument.parse(files.load("schemaVersion: 1\noverrides:\n- {match: {type: Cipher}, set: {keySize: [1]}}\n")) }.message)
    }

    @Test
    fun aPolicyValueOutsideTheChoicesIsRefused() {
        assertEquals("invalid: policy.onFailure retry, one of [stop, skip]",
            assertThrows(IllegalArgumentException::class.java) { GlobalDocument.parse(files.load("schemaVersion: 1\nselection: {testSet: a.yaml}\npolicy: {onFailure: retry}\n")) }.message)
        assertEquals("unknown_keys: policy [onUnavailable], known [onFailure]",
            assertThrows(IllegalArgumentException::class.java) { GlobalDocument.parse(files.load("schemaVersion: 1\nselection: {testSet: a.yaml}\npolicy: {onUnavailable: skip}\n")) }.message)
    }

    @Test
    fun aMissingRunSectionOrKeyKeepsDefaults() {
        val minimal = GlobalDocument.parse(files.load("schemaVersion: 1\nselection: {testSet: testsets/all.yaml}\n"))
        assertEquals(listOf(1024), minimal.run.inputSizes)
        val partial = GlobalDocument.parse(files.load("schemaVersion: 1\nselection: {testSet: testsets/all.yaml}\nrun: {processRepetitions: 3}\n"))
        assertEquals(3, partial.run.processRepetitions)
        assertEquals(listOf(1024), partial.run.inputSizes)
    }

    @Test
    fun aKeyWrittenTwiceIsRejected() {
        val message = assertThrows(RuntimeException::class.java) { files.load("schemaVersion: 1\nschemaVersion: 1\n") }.message!!
        assertTrue(message, message.contains("duplicate key"))
    }
}
