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
    private val testSet = File(directory, "config/testsets/default_predefined.yaml").apply { parentFile.mkdirs(); writeText(Fixtures.TEST_SET) }
    private val configuration = Configuration(File(directory, "configuration"))

    /** The inventory is regenerated on every probe; authored files are never written. */
    @Test
    fun aProbeOverwritesOnlyTheInventory() {
        val globalBefore = global.readText()
        configuration.inventory(capture, trial).appendText("# stale\n")
        configuration.inventory(capture, trial)
        configuration.effective(global, notes = emptyList())
        assertTrue(!configuration.inventoryFile.readText().contains("# stale"))
        assertEquals(globalBefore, global.readText())
    }

    /** A missing or broken file is named, and a missing test set names the setting that pointed there. */
    @Test
    fun aBadFileIsNamed() {
        configuration.inventory(capture, trial)
        val missingGlobal = File(directory, "nowhere/global.yaml")
        assertEquals("missing_file: ${missingGlobal.path}", assertThrows(IllegalArgumentException::class.java) { configuration.effective(missingGlobal, notes = emptyList()) }.message)

        global.writeText(Fixtures.GLOBAL.replace("testsets/default_predefined.yaml", "testsets/predefine.yaml"))
        val missingTestSet = assertThrows(IllegalArgumentException::class.java) { configuration.effective(global, notes = emptyList()) }.message!!
        assertTrue(missingTestSet, missingTestSet.startsWith("missing_file: ") && missingTestSet.endsWith("(global.yaml selection.testSet: testsets/predefine.yaml)"))

        global.writeText(Fixtures.GLOBAL)
        testSet.writeText(Fixtures.TEST_SET.replace("- {type: Cipher, name: RSA}", "- {type: Cipher, nme: RSA}"))
        val insideTheFile = assertThrows(IllegalArgumentException::class.java) { configuration.effective(global, notes = emptyList()) }.message!!
        assertTrue(insideTheFile, insideTheFile.startsWith("unknown_keys: default_predefined.yaml: include[1] [nme]"))
    }

    /** A failed run must not leave the previous run's effective.yaml for preparation to pick up. */
    @Test
    fun aFailedRunLeavesNoStaleEffectiveFile() {
        configuration.inventory(capture, trial)
        configuration.effective(global, notes = emptyList())
        assertTrue(configuration.effectiveFile.exists())
        global.writeText(Fixtures.GLOBAL.replace("policy: {onFailure: skip}", "policy: {onFailure: stop}"))
        assertThrows(IllegalStateException::class.java) { configuration.effective(global, notes = emptyList()) }
        assertFalse(configuration.effectiveFile.exists())
        assertFalse(configuration.reportFile.exists())
    }

    @Test
    fun theRuntimeNotesLeadTheReportWarnings() {
        configuration.inventory(capture, trial)
        configuration.effective(global, notes = listOf("bundled_android_only: g:a:1 (A): not installed"))
        assertEquals("bundled_android_only: g:a:1 (A): not installed", configuration.readEffective().warnings.first())
    }

    /** Warnings and skips live in report.yaml beside effective.yaml, and reading the effective settings joins them back. */
    @Test
    fun whatTheRunNoticedIsWrittenBesideTheSettingsAndJoinedOnRead() {
        configuration.inventory(capture, trial)
        configuration.effective(global, notes = emptyList())
        assertTrue(configuration.reportFile.exists())
        val settings = configuration.effectiveFile.readText()
        assertTrue(settings, !settings.contains("warnings:") && !settings.contains("skipped:"))
        configuration.reportFile.writeText(configuration.reportFile.readText().replace("warnings: []", "warnings: [typo_in_a_rule]"))
        assertEquals(listOf("typo_in_a_rule"), configuration.readEffective().warnings)
    }

    @Test
    fun aTrialOfAnotherCaptureIsRefused() {
        trial.writeText(trial.readText().replace("capturedAtMillis: 1700000000000", "capturedAtMillis: 1"))
        val refused = assertThrows(IllegalArgumentException::class.java) { configuration.inventory(capture, trial) }.message
        assertEquals("mismatched_trial: capture 1700000000000, trial 1", refused)
    }

    @Test
    fun anAbsoluteTestSetPathIsUsedAsGiven() {
        configuration.inventory(capture, trial)
        global.writeText(Fixtures.GLOBAL.replace("testsets/default_predefined.yaml", testSet.absolutePath))
        assertEquals("effective.yaml", configuration.effective(global, notes = emptyList()).name)
    }
}
