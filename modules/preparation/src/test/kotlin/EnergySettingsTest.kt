package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.settings.EnergySettings
import io.github.junekim0007.cryptobench.settings.HarnessSettings
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

class EnergySettingsTest {

    @Test
    fun energyIsReadFromTheHarnessAndMergedFieldByField() {
        val run = HarnessSettings.read(mapOf("energy" to mapOf("capture" to "measured", "windowSeconds" to 10)), "run.harness")
        val entry = HarnessSettings.read(mapOf("energy" to mapOf("capture" to "dry")), "entry.harness")
        assertEquals(EnergySettings("dry", 10), run.mergedWith(entry).energy)
        assertEquals(mapOf("capture" to "dry", "windowSeconds" to 10), run.mergedWith(entry).energy.let { EnergySettings.ENERGY.write(it) })
    }

    @Test
    fun aMalformedEnergyBlockNamesItsPath() {
        val failure = assertThrows(IllegalArgumentException::class.java) {
            HarnessSettings.read(mapOf("energy" to mapOf("capture" to "always")), "run.harness")
        }
        assertEquals("invalid: energy.capture always, known [none, measured, dry] at run.harness.energy", failure.message)
        assertEquals(EnergySettings(), HarnessSettings().energy)
    }
}
