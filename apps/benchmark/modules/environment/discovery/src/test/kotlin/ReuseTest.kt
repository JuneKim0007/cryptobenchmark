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
import io.github.junekim0007.cryptobench.document.YamlCodec
import io.github.junekim0007.cryptobench.files.StampedName
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
        assertEquals("missing_file: ${directory.named(StampedName.TRIAL, captureFile).path}", reason())
        directory.named(StampedName.TRIAL, captureFile).writeText("broken: [")
        assertEquals("unreadable_yaml: ${directory.named(StampedName.TRIAL, captureFile).name}: while parsing a flow node", reason())
    }

    /** A trial written before the keystore trial has no keystore section: it is refused and the device probes again. */
    @Test
    fun aTrialWithoutTheKeystoreSectionIsNotReused() {
        val captureFile = written(FIRST, withTrial = false)
        TrialYamlWriter(directory).write(TrialReport(FIRST))
        RequirementYamlWriter(directory).write(RequirementReport(FIRST, FIRST))
        assertEquals("missing_field: ${directory.named(StampedName.TRIAL, captureFile).name}: keystore", reason())
    }

    @Test
    fun aCaptureWithoutItsRequirementsIsNotReused() {
        val captureFile = written(FIRST)
        directory.named(StampedName.REQUIREMENTS, captureFile).delete()
        assertEquals("missing_file: ${directory.named(StampedName.REQUIREMENTS, captureFile).path}", reason())
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
    fun anEmptyCaptureIsNotAMapping() {
        val captureFile = written(FIRST)
        captureFile.writeText("")
        assertEquals("not_a_mapping: ${captureFile.name}: the document is not a set of key: value entries", reason())
    }

    @Test
    fun aStoredFileWithADuplicateKeyOrAnotherSchemaIsRefusedByName() {
        val captureFile = written(FIRST)
        val trialFile = directory.named(StampedName.TRIAL, captureFile)
        trialFile.appendText("capturedAtMillis: $FIRST\n")
        assertTrue(reason(), reason().startsWith("unreadable_yaml: ${trialFile.name}: while constructing a mapping"))
        captureFile.writeText(captureFile.readText().replace("schemaVersion: 1", "schemaVersion: 99"))
        assertEquals("unsupported_schema_version: ${captureFile.name}: 99, this build reads 1", reason())
    }

    /** An unreadable file fails outside the versioned read's codes: Reprobe names it and the exception. */
    @Test
    fun anUnreadableCaptureIsRefusedWithoutACode() {
        val captureFile = written(FIRST)
        captureFile.setReadable(false)
        assertTrue(reason(), reason().startsWith("invalid: refusal without a code: ${captureFile.name}: FileNotFoundException: "))
    }

    @Test
    fun aTrialOfAnotherCaptureIsNotReused() {
        val captureFile = written(FIRST, withTrial = false)
        TrialYamlWriter(directory).write(TrialReport(FIRST + 1_000, keystore = KeystoreSection(absent = "not_supported: x"))).renameTo(directory.named(StampedName.TRIAL, captureFile))
        RequirementYamlWriter(directory).write(RequirementReport(FIRST + 1_000, FIRST + 1_000)).renameTo(directory.named(StampedName.REQUIREMENTS, captureFile))
        assertEquals("${directory.named(StampedName.TRIAL, captureFile).name}, ${directory.named(StampedName.REQUIREMENTS, captureFile).name}: not written with ${captureFile.name}", reason())
    }

    @Test
    fun requirementsOfAnotherCaptureAreNotReused() {
        val captureFile = written(FIRST, withTrial = false)
        TrialYamlWriter(directory).write(TrialReport(FIRST, keystore = KeystoreSection(absent = "not_supported: x")))
        RequirementYamlWriter(directory).write(RequirementReport(FIRST + 1_000, FIRST + 1_000)).renameTo(directory.named(StampedName.REQUIREMENTS, captureFile))
        assertEquals("${directory.named(StampedName.TRIAL, captureFile).name}, ${directory.named(StampedName.REQUIREMENTS, captureFile).name}: not written with ${captureFile.name}", reason())
    }

    /** A host requirements file is above SnakeYAML's 3 MiB default and is reused. */
    @Test
    fun aRequirementsFileAboveThreeMebibytesIsReused() {
        val requirementsFile = directory.named(StampedName.REQUIREMENTS, written(FIRST))
        requirementsFile.appendText("padding:\n" + LINE.repeat(4 * MIB / LINE.length))
        assertEquals(requirementsFile.name, reused().requirementsFile.name)
    }

    private companion object {
        val RUNTIME = RuntimeInfo(model = "Pixel 9", sdkInt = 37)
        val CAPTURE = ProviderProbe().capture(Security.getProviders())
        const val FIRST = 1_750_000_000_000L
        const val MIB = 1024 * 1024
        val LINE = "- " + "a".repeat(61) + "\n"
    }
}
