package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.settings.HarnessSettings
import io.github.junekim0007.cryptobench.settings.EnergySettings
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class EnergySettingsTest {

    @Test
    fun aNarrowRuleKeepsTheEnergyFieldsABroadOneSet() {
        val broad = HarnessSettings(energy = EnergySettings(capture = "measured", windowSeconds = 10))
        val narrow = HarnessSettings(iterations = 200, energy = EnergySettings(capture = "dry"))
        assertEquals(EnergySettings(capture = "dry", windowSeconds = 10), broad.mergedWith(narrow).energy)
        assertEquals(200, broad.mergedWith(narrow).iterations)
    }

    @Test
    fun energyRoundTripsThroughTheHarnessDocument() {
        val harness = HarnessSettings(profiling = "none", energy = EnergySettings("dry", 10, 2, 5))
        assertEquals(harness, HarnessSettings.read(HarnessSettings.write(harness), "run.harness"))
    }

    @Test
    fun anUnsetEnergyBlockIsNotWritten() {
        assertTrue(HarnessSettings().isEmpty)
        assertEquals(mapOf("iterations" to 5), HarnessSettings.write(HarnessSettings(iterations = 5)))
    }
}
