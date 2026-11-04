package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.adapter.DiscoveryCapability
import io.github.junekim0007.cryptobench.preparation.device.CaptureFile
import io.github.junekim0007.cryptobench.preparation.device.TrialFile
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
        assertEquals(listOf("SUN", "SunJCE"), capability.providers())
    }

    /** A trial describes one capture; pairing it with another would answer for a different device state. */
    @Test
    fun refusesATrialOfAnotherCapture() {
        val capture = CaptureFile.read(captureFile)
        val trial = TrialFile.read(trialFile)
        val error = assertThrows(IllegalArgumentException::class.java) {
            DiscoveryCapability(capture.copy(capturedAtMillis = trial.capturedAtMillis + 1), trial)
        }
        assertTrue(error.message!!.startsWith("mismatched_trial"))
    }

    /**
     * Each of the three inbound files names itself when it refuses: one shared reader, three schemas,
     * and the version a build reads is the version it says it reads.
     */
    @Test
    fun eachInboundFileRefusesAVersionThisBuildDoesNotRead() {
        fun refusal(block: () -> Any) = assertThrows(IllegalArgumentException::class.java) { block() }.message
        assertEquals(
            "unsupported_capture_schema: probe.yaml: 99, this build reads ${CaptureFile.SUPPORTED_SCHEMA_VERSION}",
            refusal { CaptureFile.read("probe.yaml", "schemaVersion: 99\n") },
        )
        assertEquals(
            "unsupported_trial_schema: trial.yaml: 99, this build reads ${TrialFile.SUPPORTED_SCHEMA_VERSION}",
            refusal { TrialFile.read("trial.yaml", "schemaVersion: 99\n") },
        )
        assertEquals("missing_file: nowhere.yaml", refusal { CaptureFile.read(File("nowhere.yaml")) })
        val unreadable = refusal { CaptureFile.read("probe.yaml", "schemaVersion: : 1\n") }!!
        assertTrue(unreadable, unreadable.startsWith("unreadable_yaml: probe.yaml: mapping values are not allowed here"))
    }
}
