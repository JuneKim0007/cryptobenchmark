package io.github.junekim0007.cryptobench.discovery

import io.github.junekim0007.cryptobench.discovery.adapter.ProviderProbe
import io.github.junekim0007.cryptobench.contract.trial.KeystoreSection
import io.github.junekim0007.cryptobench.contract.requirements.RequirementReport
import io.github.junekim0007.cryptobench.contract.capture.RuntimeInfo
import io.github.junekim0007.cryptobench.contract.trial.TrialReport
import io.github.junekim0007.cryptobench.discovery.write.EnvironmentYamlWriter
import io.github.junekim0007.cryptobench.discovery.write.ProbeDirectory
import io.github.junekim0007.cryptobench.discovery.write.RequirementYamlWriter
import io.github.junekim0007.cryptobench.discovery.write.TrialYamlWriter
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
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
            TrialYamlWriter(directory).write(TrialReport(capturedAtMillis, keystore = KeystoreSection(absent = "not_supported: x")))
            RequirementYamlWriter(directory).write(RequirementReport(capturedAtMillis, capturedAtMillis))
        }
        return EnvironmentYamlWriter(directory).write(capture)
    }

    private fun reused(runtime: RuntimeInfo = RUNTIME): ReusedRun = discovery.reusable(runtime) as ReusedRun

    private fun reason(runtime: RuntimeInfo = RUNTIME): String = (discovery.reusable(runtime) as Reprobe).reason

    private fun sibling(captureFile: File, prefix: String): File = File(captureFile.parentFile, captureFile.name.replace("probe_", prefix))

    /** A capture describes one device: another device must probe for itself. */
    @Test
    fun onlyThisDevicesCaptureIsReused() {
        val captureFile = written(FIRST)
        val reused = reused()
        assertEquals(RUNTIME, reused.capture.runtime)
        listOf(reused.captureFile, reused.trialFile, reused.requirementsFile).forEach { assertEquals(true, it.isFile) }
        assertEquals("${captureFile.name}: captured on another runtime", reason(RUNTIME.copy(model = "Pixel 10")))
        assertEquals("${captureFile.name}: captured on another runtime", (discovery.reusable() as Reprobe).reason)
    }

    @Test
    fun nothingToReuseWithoutATrialOrAnyCapture() {
        assertEquals("no capture in ${directory.root.path}", reason())
        val captureFile = written(FIRST, withTrial = false)
        assertEquals("missing_file: ${sibling(captureFile, "trial_").path}", reason())
        sibling(captureFile, "trial_").writeText("broken: [")
        assertEquals("unreadable_yaml: ${sibling(captureFile, "trial_").name}: while parsing a flow node", reason())
    }

    /** A trial written before the keystore trial has no keystore section: it is refused and the device probes again. */
    @Test
    fun aTrialWithoutTheKeystoreSectionIsNotReused() {
        val captureFile = written(FIRST, withTrial = false)
        TrialYamlWriter(directory).write(TrialReport(FIRST))
        RequirementYamlWriter(directory).write(RequirementReport(FIRST, FIRST))
        assertEquals("missing_field: ${sibling(captureFile, "trial_").name}: keystore", reason())
    }

    @Test
    fun aCaptureWithoutItsRequirementsIsNotReused() {
        val captureFile = written(FIRST)
        sibling(captureFile, "requirements_").delete()
        assertEquals("missing_file: ${sibling(captureFile, "requirements_").path}", reason())
    }

    @Test
    fun anOtherBuildOrACaptureWithoutTheBuildIdentityIsNotReused() {
        val captureFile = written(FIRST)
        assertEquals("${captureFile.name}: captured on another runtime", reason(RUNTIME.copy(fingerprint = "a/b/c:17/X/1:user/release-keys")))
        assertEquals("${captureFile.name}: captured on another runtime", reason(RUNTIME.copy(javaVendor = "Other", javaRuntimeVersion = "17.0.1+1")))
    }

    @Test
    fun theNewestCaptureWins() {
        written(FIRST)
        val newest = written(FIRST + 1_000)
        assertEquals(newest.name, reused().captureFile.name)
    }

    @Test
    fun anEmptyCaptureIsRefusedWithoutACode() {
        written(FIRST).writeText("")
        assertTrue(reason(), reason().startsWith("invalid: refusal without a code: probe_"))
    }

    @Test
    fun aTrialOfAnotherCaptureIsNotReused() {
        val captureFile = written(FIRST, withTrial = false)
        TrialYamlWriter(directory).write(TrialReport(FIRST + 1_000, keystore = KeystoreSection(absent = "not_supported: x"))).renameTo(sibling(captureFile, "trial_"))
        RequirementYamlWriter(directory).write(RequirementReport(FIRST + 1_000, FIRST + 1_000)).renameTo(sibling(captureFile, "requirements_"))
        assertEquals("${sibling(captureFile, "trial_").name}, ${sibling(captureFile, "requirements_").name}: not written with ${captureFile.name}", reason())
    }

    /** A host requirements file is above SnakeYAML's 3 MiB default; one past the codec's limit is refused by name. */
    @Test
    fun aRequirementsFileAboveThreeMebibytesIsReusedAndOnePastTheLimitIsRefused() {
        val requirementsFile = sibling(written(FIRST), "requirements_")
        requirementsFile.appendText("padding:\n" + LINE.repeat(4 * MIB / LINE.length))
        assertEquals(requirementsFile.name, reused().requirementsFile.name)
        requirementsFile.appendText(LINE.repeat(12 * MIB / LINE.length + 1))
        assertEquals("unreadable_yaml: ${requirementsFile.name}: The incoming YAML document exceeds the limit: ${16 * MIB} code points.", reason())
    }

    private companion object {
        val RUNTIME = RuntimeInfo(model = "Pixel 9", sdkInt = 37)
        val CAPTURE = ProviderProbe().capture(Security.getProviders())
        const val FIRST = 1_750_000_000_000L
        const val MIB = 1024 * 1024
        val LINE = "- " + "a".repeat(61) + "\n"
    }
}
