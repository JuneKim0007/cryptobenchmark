package io.github.junekim0007.cryptobench.config

import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
import java.io.File

/** The module runs on its own example files, with no other module on the classpath. */
class ExampleFilesTest {

    @get:Rule
    val output = TemporaryFolder()

    private val example = File("example")

    @Test
    fun theExamplesProduceTheCommittedInventoryAndEffective() {
        val configuration = Configuration(output.root)
        configuration.inventory(File(example, "config_capture_example.yaml"), File(example, "config_trial_example.yaml"))
        configuration.effective(File(example, "config_global_example.yaml"))

        assertExample("config_inventory_example.yaml", configuration.inventoryFile)
        assertExample("config_effective_example.yaml", configuration.effectiveFile)
    }

    private fun assertExample(name: String, written: File) {
        val committed = File(example, name)
        if (System.getProperty("examples.update") != null) {
            written.copyTo(committed, overwrite = true)
            return
        }
        assertEquals("$name is not what this build writes; rerun with -Dexamples.update", committed.readText(), written.readText())
    }

    @Test
    fun theEffectiveExampleSelectsTheThreePrimitives() {
        val configuration = Configuration(output.root)
        configuration.inventory(File(example, "config_capture_example.yaml"), File(example, "config_trial_example.yaml"))
        configuration.effective(File(example, "config_global_example.yaml"))
        val effective = configuration.readEffective()
        assertEquals(setOf("SUN", "SunJCE"), effective.providers.keys)
        assertEquals(listOf("SHA-256"), effective.providers.getValue("SUN").getValue("MessageDigest").keys.toList())
        assertEquals(
            listOf("AES/GCM/NoPadding", "HmacSHA256"),
            effective.providers.getValue("SunJCE").values.flatMap { it.keys }.sorted(),
        )
    }
}
