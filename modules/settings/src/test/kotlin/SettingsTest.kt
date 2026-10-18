import io.github.junekim0007.cryptobench.settings.CpuRequest
import io.github.junekim0007.cryptobench.settings.EnergySettings
import io.github.junekim0007.cryptobench.settings.Facts
import io.github.junekim0007.cryptobench.settings.HarnessSettings
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test

class SettingsTest {

    private val cores = listOf(Facts.Core(0, true, 2_000_000), Facts.Core(7, true, 3_800_000), Facts.Core(3, false, null))
    private val pinnable = Facts(sdkInt = 37, rooted = false, cores = cores, pinning = true)

    private fun harness(cpu: Map<String, Any>) = HarnessSettings.read(mapOf("iterations" to 20, "cpu" to cpu), "run.harness")

    @Test
    fun aHarnessRoundTripsThroughItsTable() {
        val harness = HarnessSettings(iterations = 20, profiling = "none", energy = EnergySettings(capture = "dry"), cpu = CpuRequest("big", true))
        assertEquals(harness, HarnessSettings.read(HarnessSettings.write(harness), "run.harness"))
    }

    @Test
    fun aLaterValueWinsKeyByKeyAndNestedSectionsMergeFieldByField() {
        val run = HarnessSettings(iterations = 50, energy = EnergySettings(capture = "dry", windowSeconds = 10))
        val entry = HarnessSettings(energy = EnergySettings(capture = "measured"), cpu = CpuRequest("7"))
        assertEquals(HarnessSettings(iterations = 50, energy = EnergySettings(capture = "measured", windowSeconds = 10), cpu = CpuRequest("7")),
            run.mergedWith(entry))
    }

    @Test
    fun eachMissingFactNamesWhyACoreCannotBePinned() {
        fun reason(facts: Facts, core: String) = HarnessSettings.HARNESS.unsupported(harness(mapOf("core" to core)), facts, "run.harness").single().reason
        assertTrue(reason(Facts.UNKNOWN, "big").startsWith("facts_unknown:"))
        assertTrue(reason(pinnable.copy(pinning = false), "big").startsWith("no_pinning:"))
        assertTrue(reason(pinnable, "3").startsWith("no_core:"))
        assertTrue(reason(pinnable.copy(cores = listOf(Facts.Core(0, true, null))), "big").startsWith("no_frequencies:"))
    }

    @Test
    fun aSupportedRequestStaysAndAnUnsupportedOneIsRemovedWhole() {
        val wanted = harness(mapOf("core" to "big", "required" to true))
        assertTrue(HarnessSettings.HARNESS.unsupported(wanted, pinnable, "run.harness").isEmpty())
        val missing = HarnessSettings.HARNESS.unsupported(wanted, Facts.UNKNOWN, "run.harness")
        assertEquals(listOf("run.harness.cpu"), missing.map { it.path })
        val kept = HarnessSettings.HARNESS.supported(wanted, missing, "run.harness")
        assertNull(kept.cpu)
        assertEquals(20, kept.iterations)
    }

    @Test
    fun aCpuBlockRefusesUnknownKeysAndBadCores() {
        assertThrows(IllegalArgumentException::class.java) { harness(mapOf("core" to "big", "pin" to true)) }
        assertThrows(IllegalArgumentException::class.java) { harness(mapOf("core" to "fast")) }
        assertThrows(IllegalArgumentException::class.java) { harness(mapOf("required" to true)) }
    }

    @Test
    fun factsReadFromTheirFile() {
        val facts = Facts.read(mapOf("schemaVersion" to 1, "os" to mapOf("sdkInt" to 37), "rooted" to false, "pinning" to true,
            "cpu" to mapOf("cores" to listOf(mapOf("core" to 7, "online" to true, "maxKhz" to 3_782_000)))))
        assertEquals(Facts(37, false, listOf(Facts.Core(7, true, 3_782_000)), true), facts)
    }
}
