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
        assertEquals(listOf("GHOST/ECB/NOPADDING", "GHOST/CBC/NOPADDING"), ghost.transformations.map { it.name })
        assertTrue(ghost.transformations.none { it.outcome.instantiates })
        assertEquals("the report belongs to the capture it was run on", capture.capturedAtMillis, report.capturedAtMillis)
    }

    @Suppress("DEPRECATION")
    private val bare = object : Provider("Bare", 1.0, "a bare cipher without modes or paddings, and a registered transformation") {
        init {
            put("Cipher.AES", javax.crypto.Cipher.getInstance("AES/ECB/NoPadding").provider.getService("Cipher", "AES").className)
            put("Cipher.AES/CBC/NoPadding", "no.such.Cbc")
        }
    }

    @Suppress("DEPRECATION")
    private val naming = object : Provider("Naming", 1.0, "registers transformations by name") {
        init {
            put("Cipher.AES/GCM/NoPadding", "no.such.Gcm")
            put("Cipher.AES/CBC/NoPadding", "no.such.Cbc")
            put("Cipher.AES/FOO/NoPadding", "no.such.Foo")
        }
    }

    /** A cipher declaring no modes or paddings tries the transformations other providers register for its base, but none its own provider registers. */
    @Test
    fun aBareCipherTriesWhatOtherProvidersNameForItsBase() {
        val capture = ProviderProbe().capture(arrayOf(bare, naming, fake))
        val report = TrialRunner().run(capture, arrayOf(bare, naming, fake))
        val aes = report.services.single { it.provider == "Bare" && it.algorithm == "AES" }
        assertEquals(listOf("AES/FOO/NoPadding", "AES/GCM/NoPadding"), aes.transformations.map { it.name }.sorted())
        assertFalse("a mode the provider refuses is recorded, not thrown", aes.transformations.single { it.name == "AES/FOO/NoPadding" }.outcome.instantiates)
        assertEquals(listOf("GHOST/ECB/NOPADDING", "GHOST/CBC/NOPADDING"), report.services.single { it.algorithm == "GHOST" }.transformations.map { it.name })
        assertTrue(report.services.filter { it.provider == "Naming" }.all { it.transformations.isEmpty() })
    }

    @Test
    fun aCaptureFromAnotherDeviceNamesTheMissingProvider() {
        val capture = ProviderProbe().capture(arrayOf(fake))
        val report = TrialRunner().run(capture, emptyArray())
        assertEquals("provider_not_installed", report.services.single().outcome.error)
    }
}
