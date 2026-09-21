package io.github.junekim0007.cryptobench.config

import org.junit.Assert.assertEquals
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
}
