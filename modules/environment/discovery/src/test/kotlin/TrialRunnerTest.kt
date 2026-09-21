package io.github.junekim0007.cryptobench.discovery

import io.github.junekim0007.cryptobench.discovery.adapter.ProviderProbe
import io.github.junekim0007.cryptobench.discovery.trial.TrialRunner
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import java.security.Provider

class TrialRunnerTest {

    @Suppress("DEPRECATION")
    private val fake = object : Provider("Fake", 1.0, "declares a class that does not exist") {
        init {
            put("Cipher.GHOST", "no.such.Ghost")
            put("Cipher.GHOST SupportedModes", "ECB|CBC")
            put("Cipher.GHOST SupportedPaddings", "NOPADDING")
        }
    }

    /** The property map is the provider's claim; the trial records what happens when the claim is called. */
    @Test
    fun aDeclaredClassThatDoesNotExistIsRecordedNotThrown() {
        val capture = ProviderProbe().capture(arrayOf(fake))
        val report = TrialRunner().run(capture, arrayOf(fake))
        val ghost = report.services.single()
        assertFalse(ghost.outcome.instantiates)
        assertTrue(ghost.outcome.error, ghost.outcome.error.startsWith("NoSuchAlgorithmException"))
        assertEquals(listOf("GHOST", "GHOST/ECB/NOPADDING", "GHOST/CBC/NOPADDING"), ghost.transformations.map { it.name })
        assertTrue(ghost.transformations.none { it.outcome.instantiates })
    }

    @Test
    fun aCaptureFromAnotherDeviceNamesTheMissingProvider() {
        val capture = ProviderProbe().capture(arrayOf(fake))
        val report = TrialRunner().run(capture, emptyArray())
        assertEquals("provider_not_installed", report.services.single().outcome.error)
    }

    @Test
    fun theReportSharesTheCaptureInstant() {
        val capture = ProviderProbe().capture(arrayOf(fake), capturedAtMillis = 1_700_000_000_000L)
        assertEquals(1_700_000_000_000L, TrialRunner().run(capture, arrayOf(fake)).capturedAtMillis)
    }
}
