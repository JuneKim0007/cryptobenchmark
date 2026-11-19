package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.config.layers.LayerStack
import io.github.junekim0007.cryptobench.document.YamlCodec
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
import java.io.File

class LayerStackTest {

    @get:Rule
    val folder = TemporaryFolder()

    // the config module's own examples, from its build or from cli's, which compiles these tests too
    private val example = listOf(File("example"), File("../modules/config/example")).first { File(it, "config_global_example.yaml").isFile }

    private fun file(name: String, text: String): File = File(folder.root, name).apply { parentFile.mkdirs(); writeText(text) }

    private fun refused(composition: File): String = assertThrows(IllegalArgumentException::class.java) { AuthoredFiles().read(composition) }.message!!

    @Test
    fun mappingsMergeByKeyListsAndScalarsReplaceAndPassesReplaceWhole() {
        file("base.yaml", "schemaVersion: 1\nselection: {testSet: t.yaml, exclude: [{provider: A}]}\n" +
            "run: {orderSeed: 1, seed: 3, metrics: [TIME, ALLOCATION], passes: {timing: {samples: 5}, allocation: {samples: 2}}}\n")
        file("overlays/energy.yaml", "run: {seed: 4, passes: {timing: {samples: 7}}}\nselection: {exclude: [{provider: B}]}\n")
        val composition = file("energy.yaml", "schemaVersion: 1\nlayers: [base.yaml, overlays/energy.yaml]\nselection: {testSet: other.yaml}\n")
        val merged = LayerStack.read(composition)
        @Suppress("UNCHECKED_CAST")
        val run = merged.document["run"] as Map<String, Any>
        assertEquals(mapOf("timing" to mapOf("samples" to 7)), run["passes"])
        assertEquals(listOf(4, 1, listOf("TIME", "ALLOCATION")), listOf(run["seed"], run["orderSeed"], run["metrics"]))
        assertEquals(mapOf("testSet" to "other.yaml", "exclude" to listOf(mapOf("provider" to "B"))), merged.document["selection"])
        assertEquals(listOf("base.yaml", "overlays/energy.yaml", "energy.yaml"), merged.layers.map { it.path })
        assertEquals(mapOf("run.passes.timing.samples" to 2, "run.seed" to 2, "run.orderSeed" to 1, "selection.testSet" to 3),
            merged.sources.filterKeys { it in setOf("run.passes.timing.samples", "run.seed", "run.orderSeed", "selection.testSet") })
        assertEquals(null, merged.sources["run.passes.allocation.samples"])
    }

    /** An overlay that writes run.passes replaces the whole block, its pass gates too; a pass gate leaf it does not write is the run gate's, named via it. */
    @Test
    fun aPassGateLeafItDoesNotWriteIsNamedFromTheRunGate() {
        listOf("config_capture_example.yaml", "config_trial_example.yaml").forEach { File(example, it).copyTo(File(folder.root, it)) }
        file("t.yaml", "schemaVersion: 1\n")
        file("base.yaml", "schemaVersion: 1\nselection: {testSet: t.yaml}\nrun: {orderSeed: 1, thermalGate: {temperatureKeptCelsius: 36.0, pollMinutes: 2}, " +
            "passes: {energy: {samples: 5, caseCooldownSeconds: 9}}}\n")
        file("overlays/energy.yaml", "run: {passes: {energy: {samples: 7, thermalGate: {temperatureKeptCelsius: 35.0}}}}\n")
        val composition = file("energy.yaml", "schemaVersion: 1\nlayers: [base.yaml, overlays/energy.yaml]\n")
        val configuration = Configuration(folder.newFolder("out")).apply { inventory(File(folder.root, "config_capture_example.yaml"), File(folder.root, "config_trial_example.yaml")) }
        val effective = YamlCodec.DOCUMENT.load(configuration.effective(composition).readText())
        @Suppress("UNCHECKED_CAST")
        val energy = (((effective["run"] as Map<String, Any>)["passes"]) as Map<String, Map<String, Any>>).getValue("energy")
        assertEquals(null, energy["caseCooldownSeconds"])
        @Suppress("UNCHECKED_CAST")
        val settings = (effective["generatedFrom"] as Map<String, Any>)["settings"] as Map<String, String>
        val gate = "run.passes.energy.thermalGate"
        assertEquals(listOf("layer 2 overlays/energy.yaml", "layer 1 base.yaml via run.thermalGate", "default"),
            listOf(settings["$gate.temperatureKeptCelsius"], settings["$gate.pollMinutes"], settings["$gate.discardLimit"]))
    }

    @Test
    fun aLayerThatListsLayersAKeyTypoAndAMissingLayerAreRefusedByName() {
        file("inner.yaml", "layers: [x.yaml]\n")
        assertTrue(refused(file("a.yaml", "schemaVersion: 1\nlayers: [inner.yaml]\n")).startsWith("nested_layers: inner.yaml lists layers"))
        file("base.yaml", Fixtures.seeded("schemaVersion: 1\nselection: {testSet: t.yaml}\nrun: {}\n"))
        file("typo.yaml", "run: {sed: 2}\n")
        val message = refused(file("b.yaml", "schemaVersion: 1\nlayers: [base.yaml, typo.yaml]\n"))
        assertTrue(message, message.startsWith("b.yaml: unknown_keys: run [sed]") && message.endsWith("(layer 2 typo.yaml)"))
        assertTrue(refused(file("c.yaml", "schemaVersion: 1\nlayers: [gone.yaml]\n")).startsWith("missing_file: "))
        assertTrue(refused(file("d.yaml", "layers: [base.yaml]\n")).startsWith("missing_field: d.yaml: schemaVersion"))
    }

    @Test
    fun aCompositionOfTheExampleWritesTheSameEffectiveApartFromGeneratedFrom() {
        listOf("config_global_example.yaml", "config_testset_example.yaml").forEach { File(example, it).copyTo(File(folder.root, it)) }
        val composition = file("composed.yaml", "schemaVersion: 1\nlayers: [config_global_example.yaml]\n")
        val plain = Configuration(folder.newFolder("plain")).apply { inventory(File(example, "config_capture_example.yaml"), File(example, "config_trial_example.yaml")) }
        val composed = Configuration(folder.newFolder("composed")).apply { inventory(File(example, "config_capture_example.yaml"), File(example, "config_trial_example.yaml")) }
        plain.effective(File(folder.root, "config_global_example.yaml"))
        composed.effective(composition)
        val read = { file: File -> YamlCodec.DOCUMENT.load(file.readText()) }
        assertEquals(read(plain.effectiveFile) - "generatedFrom", read(composed.effectiveFile) - "generatedFrom")
        @Suppress("UNCHECKED_CAST")
        val settings = (read(composed.effectiveFile)["generatedFrom"] as Map<String, Any>)["settings"] as Map<String, String>
        assertEquals(listOf("layer 1 config_global_example.yaml", "default"), listOf(settings["run.seed"], settings["run.variants"]))
    }
}
