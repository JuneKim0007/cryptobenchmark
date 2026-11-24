package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.files.RepositoryFiles
import io.github.junekim0007.cryptobench.files.StatedJson
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
import org.yaml.snakeyaml.LoaderOptions
import org.yaml.snakeyaml.Yaml
import org.yaml.snakeyaml.constructor.SafeConstructor
import java.io.File

/** The module runs on its own example files, with no other module on the classpath; -Dexamples.update also writes the .json tests/contracts/documents states for the global and effective examples. */
class ExampleFilesTest {

    @get:Rule
    val output = TemporaryFolder()

    private val example = File("example")

    @Test
    fun theExamplesProduceTheCommittedInventoryEffectiveAndReport() {
        val configuration = Configuration(output.root)
        configuration.inventory(File(example, "config_capture_example.yaml"), File(example, "config_trial_example.yaml"))
        configuration.effective(File(example, "config_global_example.yaml"), notes = emptyList())

        assertExample("config_inventory_example.yaml", configuration.inventoryFile)
        assertExample("config_effective_example.yaml", configuration.effectiveFile)
        assertExample("config_report_example.yaml", configuration.reportFile)
        if (System.getProperty("examples.update") != null) listOf("config_global_example", "config_effective_example").forEach { name ->
            StatedJson.write(File(RepositoryFiles.documents, "$name.json"), Yaml(SafeConstructor(LoaderOptions())).load(File(example, "$name.yaml").readText()))
        }
    }

    private fun assertExample(name: String, written: File) {
        val committed = File(example, name)
        if (System.getProperty("examples.update") != null) {
            written.copyTo(committed, overwrite = true)
            return
        }
        assertEquals("$name is not what this build writes; rerun with -Dexamples.update", committed.readText(), written.readText())
    }
}
