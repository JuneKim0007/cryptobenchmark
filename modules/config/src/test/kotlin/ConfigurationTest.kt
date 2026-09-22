package io.github.junekim0007.cryptobench.config

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File
import java.nio.file.Files

class ConfigurationTest {

    private val directory: File = Files.createTempDirectory("configuration").toFile()
    private val capture = File(directory, "discovery/probe_x.yaml").apply { parentFile.mkdirs(); writeText(Fixtures.CAPTURE) }
    private val trial = File(directory, "discovery/trial_x.yaml").apply { writeText(Fixtures.TRIAL) }
    private val global = File(directory, "config/global.yaml").apply { parentFile.mkdirs(); writeText(Fixtures.GLOBAL) }
    private val testSet = File(directory, "config/testsets/scope.yaml").apply { parentFile.mkdirs(); writeText(Fixtures.TEST_SET) }
    private val configuration = Configuration(File(directory, "configuration"))

    /** The test set path in global.yaml is resolved against global.yaml's directory, not the working directory. */
    @Test
    fun inventoryThenEffective() {
        configuration.inventory(capture, trial)
        val effective = configuration.effective(global)
        assertEquals("effective.yaml", effective.name)
        assertEquals(setOf("SunJCE", "SUN"), configuration.readEffective().providers.keys)
    }

    /** The inventory is regenerated on every probe; authored files are never written. */
    @Test
    fun aProbeOverwritesOnlyTheInventory() {
        val globalBefore = global.readText()
        configuration.inventory(capture, trial).appendText("# stale\n")
        configuration.inventory(capture, trial)
        configuration.effective(global)
        assertTrue(!configuration.inventoryFile.readText().contains("# stale"))
        assertEquals(globalBefore, global.readText())
    }

    /** The committed config/ files parse; a broken edit to them fails here. */
    @Test
    fun theCommittedConfigParses() {
        val root = generateSequence(File("").absoluteFile) { it.parentFile }.firstOrNull { File(it, "config/global.yaml").exists() }
            ?: return
        val files = io.github.junekim0007.cryptobench.config.yaml.YamlFiles()
        val committed = files.at(File(root, "config/global.yaml"), io.github.junekim0007.cryptobench.config.global.GlobalDocument).read()
        File(root, "config/testsets").listFiles { file -> file.name.endsWith(".yaml") }!!.forEach { file ->
            files.at(file, io.github.junekim0007.cryptobench.config.testset.TestSetDocument).read()
        }
        assertEquals("testsets/scope.yaml", committed.selection.testSet)
    }

    /** The setting that pointed at a missing file is named, not just the path. */
    @Test
    fun aMissingTestSetNamesTheSettingThatPointedThere() {
        configuration.inventory(capture, trial)
        global.writeText(Fixtures.GLOBAL.replace("testsets/scope.yaml", "testsets/scop.yaml"))
        val message = assertThrows(IllegalArgumentException::class.java) { configuration.effective(global) }.message!!
        assertTrue(message, message.startsWith("missing_file: ") && message.endsWith("(global.yaml selection.testSet: testsets/scop.yaml)"))
    }

    @Test
    fun aMissingGlobalFileIsNamed() {
        val missing = File(directory, "nowhere/global.yaml")
        assertEquals("missing_file: ${missing.path}", assertThrows(IllegalArgumentException::class.java) { configuration.effective(missing) }.message)
    }

    @Test
    fun anErrorInsideAFileNamesTheFile() {
        configuration.inventory(capture, trial)
        testSet.writeText(Fixtures.TEST_SET.replace("- {type: Cipher, name: RSA}", "- {type: Cipher, nme: RSA}"))
        val message = assertThrows(IllegalArgumentException::class.java) { configuration.effective(global) }.message!!
        assertTrue(message, message.startsWith("scope.yaml: unknown_keys: include[1] [nme]"))
    }

    /** A failed run must not leave the previous run's effective.yaml for preparation to pick up. */
    @Test
    fun aFailedRunLeavesNoStaleEffectiveFile() {
        configuration.inventory(capture, trial)
        configuration.effective(global)
        assertTrue(configuration.effectiveFile.exists())
        global.writeText(Fixtures.GLOBAL.replace("policy: {onFailure: skip}", "policy: {onFailure: stop}"))
        assertThrows(IllegalStateException::class.java) { configuration.effective(global) }
        assertFalse(configuration.effectiveFile.exists())
    }

    @Test
    fun anAbsoluteTestSetPathIsUsedAsGiven() {
        configuration.inventory(capture, trial)
        global.writeText(Fixtures.GLOBAL.replace("testsets/scope.yaml", testSet.absolutePath))
        assertEquals("effective.yaml", configuration.effective(global).name)
    }
}
