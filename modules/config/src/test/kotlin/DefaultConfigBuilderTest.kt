package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.config.contract.ConfigEntry
import io.github.junekim0007.cryptobench.config.generate.DefaultConfigBuilder
import io.github.junekim0007.cryptobench.config.source.CaptureSource
import io.github.junekim0007.cryptobench.config.source.TrialSource
import io.github.junekim0007.cryptobench.config.write.YamlCodec
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

class DefaultConfigBuilderTest {

    private val codec = YamlCodec()
    private val capture = CaptureSource.read("probe_x.yaml", codec.load(Fixtures.CAPTURE))
    private val trial = TrialSource.read("trial_x.yaml", codec.load(Fixtures.TRIAL))
    private val config = DefaultConfigBuilder().build(capture, trial)

    @Test
    fun providersFollowPrecedence() {
        assertEquals(listOf("SUN", "SunJCE"), config.providers.keys.toList())
    }

    /** Only names that were called with a default key appear; instantiation alone does not make an entry. */
    @Test
    fun entriesAreTheNamesWithADefaultRun() {
        val sunJce = config.providers.getValue("SunJCE")
        assertEquals(listOf("Cipher", "KeyGenerator"), sunJce.keys.toList())
        assertEquals(listOf("AES", "AES/CBC/PKCS5PADDING", "RSA"), sunJce.getValue("Cipher").keys.toList())
    }

    @Test
    fun theObservedDefaultsAreWrittenOut() {
        val cipher = config.providers.getValue("SunJCE").getValue("Cipher")
        assertEquals(
            ConfigEntry(enabled = true, keySizes = listOf(256), keyAlgorithm = "AES", keyProvider = "SunJCE", providerChose = "AES iv=16B"),
            cipher.getValue("AES/CBC/PKCS5PADDING"),
        )
        assertEquals(listOf(32), cipher.getValue("RSA").inputSizes)
        assertEquals(emptyList<Int>(), cipher.getValue("AES").inputSizes)
    }

    @Test
    fun whatDidNotRunIsDisabledWithItsReason() {
        val prf = config.providers.getValue("SunJCE").getValue("KeyGenerator").getValue("SunTlsPrf")
        assertEquals(false, prf.enabled)
        assertEquals("IllegalStateException: TlsPrfGenerator must be initialized", prf.reason)
    }

    @Test
    fun theFilesItCameFromAreRecorded() {
        assertEquals("probe_x.yaml", config.generatedFrom.capture)
        assertEquals("Pixel 9", config.generatedFrom.device["model"])
    }

    @Test
    fun aTrialOfAnotherCaptureIsRefused() {
        val other = capture.copy(capturedAtMillis = 1)
        val error = assertThrows(IllegalArgumentException::class.java) { DefaultConfigBuilder().build(other, trial) }
        assertEquals("mismatched_trial: capture 1, trial 1700000000000", error.message)
    }
}
