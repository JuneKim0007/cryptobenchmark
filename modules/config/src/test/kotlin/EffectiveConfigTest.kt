package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.config.effective.EffectiveDocument
import java.io.File
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/** The run id every file of a run can carry. */
class EffectiveConfigTest {

    private val fixture = DocumentFixture()
    private val files = fixture.files
    private val codec = fixture.codec
    private val directory = fixture.directory
    private val inventory = fixture.inventory
    private val global = fixture.global
    private val testSet = fixture.testSet
    private val effective = fixture.effective

    /** The run id is the capture's discovery stamp, so every file of a run can name the same one; a hand-named capture has none. */
    @Test
    fun theRunIdIsTheCaptureStampOrNothing() {
        val stamped = effective.copy(generatedFrom = effective.generatedFrom.copy(
            environment = effective.generatedFrom.environment.copy(capture = "probe_20261005T103349Z.yaml")))
        assertEquals("20261005T103349Z", stamped.runId)
        assertEquals(null, effective.runId)
        files.at(File(directory, "effective.yaml"), EffectiveDocument).write(stamped)
        assertTrue(File(directory, "effective.yaml").readText().contains("runId: 20261005T103349Z"))
    }
}
