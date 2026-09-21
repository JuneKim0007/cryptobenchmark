package io.github.junekim0007.cryptobench.discovery

import io.github.junekim0007.cryptobench.discovery.write.EnvironmentYamlWriter
import io.github.junekim0007.cryptobench.discovery.write.ProbeDirectory
import io.github.junekim0007.cryptobench.discovery.write.ProviderClassNameWriter
import io.github.junekim0007.cryptobench.discovery.trial.TrialRunner

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
    private val directory = ProbeDirectory(File(System.getProperty("capture.dir") ?: "build/capture"))
    private val discovery = Discovery(directory)

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
            assertTrue("$type lists no algorithms", setting.algorithms(type).isNotEmpty())
        }
    }

    @Test
    fun theCaptureKeepsItsShape() {
        val document = EnvironmentYamlWriter(directory).toDocument(capture)
        listOf("schemaVersion", "capturedAtMillis", "runtime", "providers").forEach {
            assertTrue("capture is missing $it", document.containsKey(it))
        }
    }

    /** Written out so a workflow can attach it and drift can be diffed instead of guessed. */
    @Test
    fun theFacadeWritesTheCaptureAndTheClassList() {
        val run = discovery.probe(Security.getProviders())
        assertTrue("capture not written", run.captureFile.length() > 0)
        assertTrue("unexpected name ${run.captureFile.name}", run.captureFile.name.matches(Regex("probe_\\d{8}T\\d{6}Z\\.yaml")))
        assertTrue("class list not written", run.classesFile.length() > 0)
        assertTrue("unexpected name ${run.classesFile.name}", run.classesFile.name.matches(Regex("probe_classes_\\d{8}T\\d{6}Z\\.yaml")))
        assertTrue("the capture written differs from the capture returned", run.capture == capture.copy(capturedAtMillis = run.capture.capturedAtMillis))
    }

    @Test
    fun theClassListIsDistinctAndSorted() {
        val classes = ProviderClassNameWriter(directory).toDocument(capture)
        assertTrue("no provider listed", classes.isNotEmpty())
        classes.forEach { (provider, names) ->
            assertTrue("$provider lists a class twice", names.size == names.distinct().size)
            assertTrue("$provider is not sorted", names == names.sorted())
        }
    }

    @Test
    fun theStaplesInstantiateAndSomeDeclaredTransformationsDoNot() {
        val report = TrialRunner().run(capture, Security.getProviders())
        val aes = report.services.single { it.provider == "SunJCE" && it.type == "Cipher" && it.algorithm == "AES" }
        assertTrue("SunJCE AES does not instantiate: ${aes.outcome.error}", aes.outcome.instantiates)
        assertTrue("AES/CBC/PKCS5Padding is not tried", aes.transformations.any { it.name.equals("AES/CBC/PKCS5Padding", ignoreCase = true) && it.outcome.instantiates })
        assertTrue("no declared transformation failed; the trial has nothing to add over the capture", report.services.flatMap { it.transformations }.any { !it.outcome.instantiates })
        val target = discovery.trial(capture, Security.getProviders())
        assertTrue("unexpected name ${target.name}", target.name.matches(Regex("trial_\\d{8}T\\d{6}Z\\.yaml")))
    }
}
