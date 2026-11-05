package io.github.junekim0007.cryptobench.discovery

import io.github.junekim0007.cryptobench.discovery.adapter.ProviderProbe
import io.github.junekim0007.cryptobench.discovery.contract.RequirementReport
import io.github.junekim0007.cryptobench.discovery.contract.RuntimeInfo
import io.github.junekim0007.cryptobench.discovery.contract.TrialReport
import io.github.junekim0007.cryptobench.discovery.write.EnvironmentYamlWriter
import io.github.junekim0007.cryptobench.discovery.write.ProbeDirectory
import io.github.junekim0007.cryptobench.discovery.write.RequirementYamlWriter
import io.github.junekim0007.cryptobench.discovery.write.TrialYamlWriter
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test
import java.io.File
import java.nio.file.Files
import java.security.Security

class ReuseTest {

    private val directory = ProbeDirectory(Files.createTempDirectory("reuse").toFile())
    private val discovery = Discovery(directory)

    private fun written(capturedAtMillis: Long, runtime: RuntimeInfo = RUNTIME, withTrial: Boolean = true): File {
        val capture = CAPTURE.copy(runtime = runtime, capturedAtMillis = capturedAtMillis)
        if (withTrial) {
            TrialYamlWriter(directory).write(TrialReport(capturedAtMillis))
            RequirementYamlWriter(directory).write(RequirementReport(capturedAtMillis, capturedAtMillis))
        }
        return EnvironmentYamlWriter(directory).write(capture)
    }

    /** A capture describes one device: another device must probe for itself. */
    @Test
    fun onlyThisDevicesCaptureIsReused() {
        written(FIRST)
        val reused = discovery.reusable(RUNTIME)!!
        assertEquals(RUNTIME, reused.capture.runtime)
        listOf(reused.captureFile, reused.trialFile, reused.requirementsFile).forEach { assertEquals(true, it.isFile) }
        assertNull(discovery.reusable(RUNTIME.copy(model = "Pixel 10")))
        assertNull(discovery.reusable())
    }

    @Test
    fun nothingToReuseWithoutATrialOrAnyCapture() {
        assertNull(discovery.reusable(RUNTIME))
        val captureFile = written(FIRST, withTrial = false)
        assertNull(discovery.reusable(RUNTIME))
        File(captureFile.parentFile, captureFile.name.replace("probe_", "trial_")).writeText("broken: [")
        assertNull(discovery.reusable(RUNTIME))
    }

    @Test
    fun aCaptureWithoutItsRequirementsIsNotReused() {
        val captureFile = written(FIRST)
        File(captureFile.parentFile, captureFile.name.replace("probe_", "requirements_")).delete()
        assertNull(discovery.reusable(RUNTIME))
    }

    @Test
    fun anOtherBuildOrACaptureWithoutTheBuildIdentityIsNotReused() {
        written(FIRST)
        assertNull(discovery.reusable(RUNTIME.copy(fingerprint = "a/b/c:17/X/1:user/release-keys")))
        assertNull(discovery.reusable(RUNTIME.copy(javaVendor = "Other", javaRuntimeVersion = "17.0.1+1")))
    }

    @Test
    fun theNewestCaptureWins() {
        written(FIRST)
        val newest = written(FIRST + 1_000)
        assertEquals(newest.name, discovery.reusable(RUNTIME)!!.captureFile.name)
    }

    private companion object {
        val RUNTIME = RuntimeInfo(model = "Pixel 9", sdkInt = 37)
        val CAPTURE = ProviderProbe().capture(Security.getProviders())
        const val FIRST = 1_750_000_000_000L
    }
}
