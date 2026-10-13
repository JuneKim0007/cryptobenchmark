package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.config.global.HarnessDocument
import io.github.junekim0007.cryptobench.config.global.dto.EnergySettings
import io.github.junekim0007.cryptobench.config.global.dto.HarnessSettings
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
        assertEquals(harness, HarnessDocument.parse(HarnessDocument.of(harness), "run.harness"))
    }

    @Test
    fun anUnsetEnergyBlockIsNotWritten() {
        assertTrue(HarnessSettings().isEmpty)
        assertEquals(mapOf("iterations" to 5), HarnessDocument.of(HarnessSettings(iterations = 5)))
    }
}
