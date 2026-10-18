import io.github.junekim0007.cryptobench.settings.CpuSettings
import io.github.junekim0007.cryptobench.settings.EnergySettings
import io.github.junekim0007.cryptobench.settings.Facts
import io.github.junekim0007.cryptobench.settings.HarnessSettings
import io.github.junekim0007.cryptobench.settings.HarnessSettings.Companion.HARNESS
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test

class SettingsTest {

    private val cores = listOf(Facts.Core(0, true, 2_000_000), Facts.Core(7, true, 3_800_000), Facts.Core(3, false, 4_000_000))
    private val pinnable = Facts(gathered = true, sdkInt = 37, rooted = false, cores = cores, pinning = true)

    private fun harness(cpu: Map<String, Any>) = HarnessSettings.read(mapOf("iterations" to 20, "cpu" to cpu), "run.harness")

    @Test
    fun aHarnessRoundTripsAndAnUnsetBlockIsNotWritten() {
        val harness = HarnessSettings(iterations = 20, profiling = "none", energy = EnergySettings("dry", 10, 2, 5), cpu = CpuSettings("7", true))
        assertEquals(harness, HarnessSettings.read(HarnessSettings.write(harness), "run.harness"))
        assertEquals(mapOf("iterations" to 5), HarnessSettings.write(HarnessSettings(iterations = 5)))
    }

    @Test
    fun nestedBlocksMergeFieldByFieldSoARuleCannotResetWhatItDoesNotName() {
        val run = HarnessSettings(iterations = 50, energy = EnergySettings(capture = "measured", windowSeconds = 10), cpu = CpuSettings("big", true))
        val rule = HarnessSettings(energy = EnergySettings(capture = "dry"), cpu = CpuSettings(core = "7"))
        val merged = run.mergedWith(rule)
        assertEquals(EnergySettings(capture = "dry", windowSeconds = 10), merged.energy)
        assertEquals(CpuSettings("7", true), merged.cpu)
    }

    @Test
    fun aBadValueNamesItsKeyAndWhere() {
        fun failure(document: Map<String, Any>) = assertThrows(IllegalArgumentException::class.java) { HarnessSettings.read(document, "run.harness") }.message
        assertEquals("invalid: energy.capture always, known [none, measured, dry] at run.harness.energy", failure(mapOf("energy" to mapOf("capture" to "always"))))
        assertEquals("not_positive: iterations 0 at run.harness", failure(mapOf("iterations" to 0)))
        assertTrue(failure(mapOf("cpu" to mapOf("core" to "fast")))!!.startsWith("invalid: cpu.core fast"))
        assertTrue(failure(mapOf("cpu" to mapOf("core" to "big", "pin" to true)))!!.startsWith("unknown_keys: run.harness.cpu [pin]"))
        assertTrue(failure(mapOf("cpu" to mapOf("core" to 64)))!!.startsWith("invalid: cpu.core 64"))
    }

    @Test
    fun eachMissingFactNamesWhyACoreCannotBePinned() {
        fun reason(facts: Facts, core: String) = HARNESS.unsupported(harness(mapOf("core" to core)), facts, "run.harness").single().reason
        assertEquals("facts_unknown: no facts.yaml for this run", reason(Facts.UNKNOWN, "big"))
        assertEquals("facts_unknown: facts.yaml has no pinning", reason(Facts(gathered = true, cores = cores), "big"))
        assertTrue(reason(pinnable.copy(pinning = false), "big").startsWith("no_pinning:"))
        assertTrue(reason(pinnable, "3").startsWith("no_core:"))
        assertTrue(reason(pinnable.copy(cores = listOf(Facts.Core(0, true, null))), "big").startsWith("no_frequencies:"))
    }

    @Test
    fun bigResolvesToTheFastestOnlineCoreAndAnUnsupportedBlockIsRemovedWhole() {
        val (kept, none) = HARNESS.forDevice(harness(mapOf("core" to "big", "required" to true)), pinnable, "run.harness")
        assertTrue(none.isEmpty())
        assertEquals(CpuSettings("7", true), kept.cpu)
        val (dropped, missing) = HARNESS.forDevice(harness(mapOf("core" to "big", "required" to true)), Facts.UNKNOWN, "run.harness")
        assertEquals(listOf("run.harness.cpu"), missing.map { it.path })
        assertTrue(missing.single().required)
        assertNull(dropped.cpu)
        assertEquals(20, dropped.iterations)
    }

    @Test
    fun factsReadFromTheirFileAndRefuseWrongTypesByName() {
        val facts = Facts.read(mapOf("schemaVersion" to 1, "os" to mapOf("sdkInt" to 37), "rooted" to false, "pinning" to true,
            "cpu" to mapOf("cores" to listOf(mapOf("core" to 7, "online" to true, "maxKhz" to 3_782_000)))))
        assertEquals(Facts(true, 37, false, listOf(Facts.Core(7, true, 3_782_000)), true), facts)
        val wrong = assertThrows(IllegalArgumentException::class.java) {
            Facts.read(mapOf("schemaVersion" to 1, "cpu" to mapOf("cores" to listOf(mapOf("core" to "seven", "online" to true)))))
        }
        assertEquals("wrong_type: facts.yaml cpu.cores[0].core expects a number", wrong.message)
    }
}
