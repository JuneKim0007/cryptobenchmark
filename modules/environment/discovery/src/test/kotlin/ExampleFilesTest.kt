package io.github.junekim0007.cryptobench.discovery

import io.github.junekim0007.cryptobench.discovery.write.CaptureDocument
import io.github.junekim0007.cryptobench.discovery.write.TrialDocument
import io.github.junekim0007.cryptobench.discovery.write.YamlCodec
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

/** The committed examples are what this build writes; a schema change that forgets them fails here. */
class ExampleFilesTest {

    private val codec = YamlCodec()

    private val example = File("example")

    private val capture = CaptureDocument.parse(codec.load(File(example, "discovery_capture_example.yaml").readText()))

    private val trial = TrialDocument.parse(codec.load(File(example, "discovery_trial_example.yaml").readText()))

    @Test
    fun theCaptureExampleSurvivesARoundTrip() {
        assertEquals(capture, CaptureDocument.parse(CaptureDocument.of(capture)))
    }

    @Test
    fun theTrialExampleSurvivesARoundTrip() {
        assertEquals(trial, TrialDocument.parse(TrialDocument.of(trial)))
    }

    @Test
    fun theTwoExamplesDescribeOneDevice() {
        assertEquals(capture.capturedAtMillis, trial.capturedAtMillis)
        assertEquals(listOf("SUN", "SunJCE"), capture.providers.map { it.name })
        assertTrue("the example should show a transformation the JCA refuses",
            trial.services.flatMap { it.transformations }.any { !it.outcome.instantiates })
        assertFalse("every captured service should be trialled",
            capture.providers.flatMap { it.services }.any { service ->
                trial.services.none { it.type == service.type && it.algorithm == service.algorithm }
            })
    }
}
