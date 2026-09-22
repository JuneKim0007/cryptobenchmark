package io.github.junekim0007.cryptobench.discovery

import io.github.junekim0007.cryptobench.discovery.contract.RuntimeInfo
import io.github.junekim0007.cryptobench.discovery.write.ProbeDirectory
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test
import java.io.File
import java.nio.file.Files
import java.security.Security

class ReuseTest {

    private val directory = ProbeDirectory(Files.createTempDirectory("reuse").toFile())
    private val discovery = Discovery(directory)
    private val runtime = RuntimeInfo(model = "Pixel 9", sdkInt = 37)

    private fun probeAndTrial() {
        val run = discovery.probe(Security.getProviders(), runtime)
        discovery.trial(run.capture, Security.getProviders())
    }

    @Test
    fun aCaptureOfThisDeviceIsReusedWithItsClassListAndTrial() {
        probeAndTrial()
        val reused = discovery.reusable(runtime)!!
        assertEquals(runtime, reused.capture.runtime)
        listOf(reused.captureFile, reused.classesFile, reused.trialFile).forEach { assertEquals(true, it.isFile) }
    }

    /** A capture describes one device: another device must probe for itself. */
    @Test
    fun aCaptureOfAnotherDeviceIsNotReused() {
        probeAndTrial()
        assertNull(discovery.reusable(runtime.copy(model = "Pixel 10")))
        assertNull(discovery.reusable())
    }

    @Test
    fun nothingToReuseWithoutATrialOrAnyCapture() {
        assertNull(discovery.reusable(runtime))
        val run = discovery.probe(Security.getProviders(), runtime)
        assertNull(discovery.reusable(runtime))
        File(run.captureFile.parentFile, run.captureFile.name.replace("probe_", "trial_")).writeText("broken: [")
        assertNull(discovery.reusable(runtime))
    }

    @Test
    fun theNewestCaptureWins() {
        probeAndTrial()
        Thread.sleep(1100)
        probeAndTrial()
        val reused = discovery.reusable(runtime)!!
        assertEquals(directory.root.listFiles()!!.filter { it.name.startsWith("probe_2") }.maxOf { it.name }, reused.captureFile.name)
    }
}
