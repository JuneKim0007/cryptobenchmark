package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.adapter.DiscoveryCapability
import io.github.junekim0007.cryptobench.contract.capture.CapturedEnvironment
import io.github.junekim0007.cryptobench.contract.capture.RuntimeInfo
import io.github.junekim0007.cryptobench.preparation.device.dto.CapturedDevice
import io.github.junekim0007.cryptobench.preparation.port.Availability
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

/** Against the example capture and trial: what the adapter answers is what the trial saw, not what the provider declared. */
class DiscoveryCapabilityTest {

    private val example = File("example")

    private val captureFile = File(example, "preparation_capture_example.yaml")

    private val trialFile = File(example, "preparation_trial_example.yaml")

    private val capability = DiscoveryCapability(captureFile, trialFile)

    private fun reason(provider: String, type: String, algorithm: String): String =
        when (val availability = capability.check(provider, type, algorithm)) {
            Availability.Available -> "available"
            is Availability.Unavailable -> availability.reason
        }

    @Test
    fun registeredNamesAliasesAndComposedTransformations() {
        assertEquals("available", reason("SunJCE", "Cipher", "AES/GCM/NoPadding"))
        assertEquals("available", reason("SunJCE", "Cipher", "AES/CBC/PKCS5Padding"))
        assertEquals("available", reason("SunJCE", "Mac", "1.2.840.113549.2.9"))
        assertEquals("available", reason("SUN", "MessageDigest", "OID.2.16.840.1.101.3.4.2.1"))
    }

    @Test
    fun declaredButRefusedIsNotAvailable() {
        assertTrue(reason("SunJCE", "Cipher", "AES/CTR/PKCS5Padding").startsWith("transformation_fails: NoSuchPaddingException"))
        // registered: the service exists, only its default-run trial failed (a key born inside its provider may still be made)
        assertTrue((capability.check("SunJCE", "Cipher", "AES/CTR/PKCS5Padding") as Availability.Unavailable).registered)
        assertEquals(false, (capability.check("SunJCE", "Cipher", "Serpent") as Availability.Unavailable).registered)
    }

    @Test
    fun namesWhyAnythingElseIsUnavailable() {
        assertEquals("provider_not_installed", reason("AndroidOpenSSL", "Cipher", "AES"))
        assertEquals("not_registered", reason("SunJCE", "Cipher", "Serpent"))
        assertEquals("not_registered", reason("SunJCE", "Cipher", "Serpent/CBC/NoPadding"))
        assertEquals("not_tried", reason("SunJCE", "Cipher", "AES/XTS/NoPadding"))
    }

    @Test
    fun providersComeInPrecedenceOrder() {
        assertEquals(listOf("SUN", "SunRsaSign", "SunJCE"), capability.providers())
    }

    /** The API level a secure case's api_too_low names is the capture's: an Android capture's sdkInt, none on a JVM's 0. */
    @Test
    fun theApiLevelIsTheCapturesAndNoneOnAJvm() {
        assertEquals(36, CapturedDevice.of(CapturedEnvironment(RuntimeInfo(sdkInt = 36))).sdkInt)
        assertEquals("android-36", CapturedDevice.of(CapturedEnvironment(RuntimeInfo(sdkInt = 36))).platform)
        assertEquals(null, CapturedDevice.of(CapturedEnvironment(RuntimeInfo(sdkInt = 0, javaVersion = "25.0.3"))).sdkInt)
        assertEquals("jdk-25", CapturedDevice.of(CapturedEnvironment(RuntimeInfo(sdkInt = 0, javaVersion = "25.0.3"))).platform)
        assertEquals(null, capability.sdkInt)
    }

    /** A trial describes one capture; pairing it with another would answer for a different device state. */
    @Test
    fun refusesATrialOfAnotherCapture() {
        val other = File.createTempFile("trial", ".yaml").apply { deleteOnExit(); writeText(trialFile.readText().replace("capturedAtMillis: 1750000000000", "capturedAtMillis: 1")) }
        val error = assertThrows(IllegalArgumentException::class.java) { DiscoveryCapability(captureFile, other) }
        assertEquals("mismatched_trial: capture 1750000000000, trial 1", error.message)
    }

    /** The pair is read through the contract's readers: their refusals name the file, preparation adds none. */
    @Test
    fun refusesWhatTheContractsReadersRefuse() {
        fun refusal(capture: File, trial: File) = assertThrows(IllegalArgumentException::class.java) { DiscoveryCapability(capture, trial) }.message
        val newer = File.createTempFile("probe", ".yaml").apply { deleteOnExit(); writeText("schemaVersion: 99\n") }
        assertEquals("unsupported_schema_version: ${newer.name}: 99, this build reads 1", refusal(newer, trialFile))
        assertEquals("missing_file: nowhere.yaml", refusal(captureFile, File("nowhere.yaml")))
    }
}
