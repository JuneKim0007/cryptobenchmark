package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.global.EnergySettings
import io.github.junekim0007.cryptobench.preparation.global.HarnessReader
import io.github.junekim0007.cryptobench.preparation.global.HarnessSettings
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

class EnergySettingsTest {

    @Test
    fun energyIsReadFromTheHarnessAndMergedFieldByField() {
        val run = HarnessReader.read(mapOf("energy" to mapOf("capture" to "measured", "windowSeconds" to 10)), "run.harness")
        val entry = HarnessReader.read(mapOf("energy" to mapOf("capture" to "dry")), "entry.harness")
        assertEquals(EnergySettings("dry", 10), run.mergedWith(entry).energy)
        assertEquals(mapOf("capture" to "dry", "windowSeconds" to 10), run.mergedWith(entry).energy.document())
    }

    @Test
    fun aMalformedEnergyBlockNamesItsPath() {
        val failure = assertThrows(IllegalArgumentException::class.java) {
            HarnessReader.read(mapOf("energy" to mapOf("capture" to "always")), "run.harness")
        }
        assertEquals("invalid: energy.capture always, known [none, measured, dry] at run.harness.energy", failure.message)
        assertEquals(EnergySettings(), HarnessSettings().energy)
    }
}
