package io.github.junekim0007.cryptobench.discovery

import io.github.junekim0007.cryptobench.discovery.write.EnvironmentYamlWriter

import io.github.junekim0007.cryptobench.discovery.adapter.ProviderProbe
import io.github.junekim0007.cryptobench.discovery.setting.DiscoverySettingConverter
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File
import java.security.Security

/**
 * What probe.md assumes about the JCA, checked against the running JVM. A failure on a new Java
 * version means the JCA moved, not that the code broke. Says nothing about Android providers (#14).
 */
class JcaContractTest {

    private val capture = ProviderProbe().capture(Security.getProviders())
    private val setting = DiscoverySettingConverter().convert(capture)

    @Test
    fun providersAreVisible() {
        assertTrue("no provider registered a service", capture.providers.any { it.services.isNotEmpty() })
        assertTrue("precedence is not 1..n", capture.providers.map { it.precedence } == (1..capture.providers.size).toList())
    }

    @Test
    fun theStapleAlgorithmsStillResolve() {
        listOf(
            "Cipher" to "AES",
            "MessageDigest" to "SHA-256",
            "Mac" to "HmacSHA256",
            "Signature" to "SHA256withRSA",
            "KeyPairGenerator" to "RSA",
        ).forEach { (type, algorithm) ->
            assertTrue("$type/$algorithm resolves to no provider", setting.providersFor(type, algorithm).isNotEmpty())
        }
    }

    @Test
    fun theCaptureKeepsItsShape() {
        val document = EnvironmentYamlWriter().toDocument(capture)
        listOf("schemaVersion", "capturedAtMillis", "runtime", "providers").forEach {
            assertTrue("capture is missing $it", document.containsKey(it))
        }
    }

    /** Written out so a workflow can attach it and drift can be diffed instead of guessed. */
    @Test
    fun writeCapture() {
        val directory = File(System.getProperty("capture.dir") ?: "build/capture")
        val target = EnvironmentYamlWriter().write(capture, directory)
        assertTrue("capture not written", target.length() > 0)
        assertTrue("unexpected name ${target.name}", target.name.matches(Regex("probe_\\d{8}T\\d{6}Z\\.yaml")))
    }
}
