package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.config.inventory.InventoryBuilder
import io.github.junekim0007.cryptobench.config.inventory.dto.InventoryEntry
import io.github.junekim0007.cryptobench.config.source.CaptureSource
import io.github.junekim0007.cryptobench.config.source.TrialSource
import io.github.junekim0007.cryptobench.config.yaml.YamlFiles
import io.github.junekim0007.cryptobench.config.yaml.YamlCodec
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

class InventoryBuilderTest {

    private val files = YamlFiles()
    private val codec = YamlCodec()
    private val capture = CaptureSource.parse(codec.load(Fixtures.CAPTURE))
    private val trial = TrialSource.parse(codec.load(Fixtures.TRIAL))
    private val names = InventoryBuilder.Files("probe_x.yaml", "trial_x.yaml")
    private val inventory = InventoryBuilder().build(capture, trial, names)

    @Test
    fun providersFollowPrecedence() {
        assertEquals(listOf("SUN", "SunJCE"), inventory.providers.keys.toList())
    }

    /** Only names environment called with a default key; instantiating alone is not an entry. */
    @Test
    fun entriesAreTheNamesWithADefaultRun() {
        assertEquals(listOf("AES", "AES/CBC/PKCS5PADDING", "RSA"), inventory.providers.getValue("SunJCE").getValue("Cipher").keys.toList())
    }

    @Test
    fun observationsAreKeptAndOnlyANeededInputSizeIsRecorded() {
        val cipher = inventory.providers.getValue("SunJCE").getValue("Cipher")
        assertEquals(InventoryEntry(runs = true, keySizes = listOf(256), keyAlgorithm = "AES", keyProvider = "SunJCE", providerChose = "AES iv=16B"), cipher.getValue("AES/CBC/PKCS5PADDING"))
        assertEquals(listOf(32), cipher.getValue("RSA").inputSizes)
        assertEquals("IllegalStateException: TlsPrfGenerator must be initialized", inventory.providers.getValue("SunJCE").getValue("KeyGenerator").getValue("SunTlsPrf").reason)
    }

    /** Which size is "the usual one" comes from the trial itself; an older trial that does not say keeps every size it observed. */
    @Test
    fun theUsualInputSizeIsTheOneTheTrialStartedFrom() {
        val cipherOf = { view: io.github.junekim0007.cryptobench.config.source.TrialView -> InventoryBuilder().build(capture, view, names).providers.getValue("SunJCE").getValue("Cipher") }
        assertEquals(emptyList<Int>(), cipherOf(trial).getValue("AES").inputSizes)
        assertEquals(listOf(1024), cipherOf(trial.copy(defaultRunInputSize = null)).getValue("AES").inputSizes)
        assertEquals(listOf(1024), cipherOf(trial.copy(defaultRunInputSize = 2048)).getValue("AES").inputSizes)
    }

    @Test
    fun aTrialOfAnotherCaptureIsRefused() {
        assertEquals("mismatched_trial: capture 1, trial 1700000000000",
            assertThrows(IllegalArgumentException::class.java) { InventoryBuilder().build(capture.copy(capturedAtMillis = 1), trial, names) }.message)
    }
}
