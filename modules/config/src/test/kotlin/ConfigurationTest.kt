package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.config.write.ConfigFile
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test
import java.io.File
import java.nio.file.Files

class ConfigurationTest {

    private val directory: File = Files.createTempDirectory("configuration").toFile()
    private val capture = File(directory, "probe_x.yaml").apply { writeText(Fixtures.CAPTURE) }
    private val trial = File(directory, "trial_x.yaml").apply { writeText(Fixtures.TRIAL) }
    private val configuration = Configuration(ConfigFile(File(directory, "configuration")))

    @Test
    fun generatesDefaultYamlAndReadsItBack() {
        val written = configuration.generate(capture, trial)
        assertEquals("default.yaml", written.name)
        assertEquals(setOf("SUN", "SunJCE"), configuration.read().providers.keys)
    }

    /** Overwriting is the current policy; #34 replaces it with keep or merge. */
    @Test
    fun aSecondGenerationOverwrites() {
        val written = configuration.generate(capture, trial)
        written.writeText(written.readText() + "# user note\n")
        configuration.generate(capture, trial)
        assertEquals(false, written.readText().contains("# user note"))
    }

    @Test
    fun anotherTrialSchemaIsRefused() {
        trial.writeText(Fixtures.TRIAL.replace("schemaVersion: 2", "schemaVersion: 1"))
        val error = assertThrows(IllegalArgumentException::class.java) { configuration.generate(capture, trial) }
        assertEquals("unsupported_trial_schema: 1, this build reads 2", error.message)
    }
}
