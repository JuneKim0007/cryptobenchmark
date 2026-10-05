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
        // the reference lists every key, so a key renamed in the schema fails here instead of misleading a reader
        val reference = files.at(File(root, "config/global.reference.yaml"), io.github.junekim0007.cryptobench.config.global.GlobalDocument).read()
        assertEquals("testsets/scope.yaml", reference.selection.testSet)
        assertEquals(50, reference.run.harness.iterations)
    }

    /** A missing or broken file is named, and a missing test set names the setting that pointed there. */
    @Test
    fun aBadFileIsNamed() {
        configuration.inventory(capture, trial)
        val missingGlobal = File(directory, "nowhere/global.yaml")
        assertEquals("missing_file: ${missingGlobal.path}", assertThrows(IllegalArgumentException::class.java) { configuration.effective(missingGlobal) }.message)

        global.writeText(Fixtures.GLOBAL.replace("testsets/scope.yaml", "testsets/scop.yaml"))
        val missingTestSet = assertThrows(IllegalArgumentException::class.java) { configuration.effective(global) }.message!!
        assertTrue(missingTestSet, missingTestSet.startsWith("missing_file: ") && missingTestSet.endsWith("(global.yaml selection.testSet: testsets/scop.yaml)"))

        global.writeText(Fixtures.GLOBAL)
        testSet.writeText(Fixtures.TEST_SET.replace("- {type: Cipher, name: RSA}", "- {type: Cipher, nme: RSA}"))
        val insideTheFile = assertThrows(IllegalArgumentException::class.java) { configuration.effective(global) }.message!!
        assertTrue(insideTheFile, insideTheFile.startsWith("scope.yaml: unknown_keys: include[1] [nme]"))
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

    /** Warnings and skips live in report.yaml beside effective.yaml, and reading the effective settings joins them back. */
    @Test
    fun whatTheRunNoticedIsWrittenBesideTheSettingsAndJoinedOnRead() {
        configuration.inventory(capture, trial)
        configuration.effective(global)
        assertTrue(configuration.reportFile.exists())
        val settings = configuration.effectiveFile.readText()
        assertTrue(settings, !settings.contains("warnings:") && !settings.contains("skipped:"))
        configuration.reportFile.writeText(configuration.reportFile.readText().replace("warnings: []", "warnings: [typo_in_a_rule]"))
        assertEquals(listOf("typo_in_a_rule"), configuration.readEffective().warnings)
    }

    @Test
    fun aFailedRunLeavesNoStaleReportEither() {
        configuration.inventory(capture, trial)
        configuration.effective(global)
        global.writeText(Fixtures.GLOBAL.replace("policy: {onFailure: skip}", "policy: {onFailure: stop}"))
        assertThrows(IllegalStateException::class.java) { configuration.effective(global) }
        assertFalse(configuration.reportFile.exists())
    }

    @Test
    fun anAbsoluteTestSetPathIsUsedAsGiven() {
        configuration.inventory(capture, trial)
        global.writeText(Fixtures.GLOBAL.replace("testsets/scope.yaml", testSet.absolutePath))
        assertEquals("effective.yaml", configuration.effective(global).name)
    }
}
