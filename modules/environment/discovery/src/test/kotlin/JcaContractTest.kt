package io.github.junekim0007.cryptobench.discovery

import io.github.junekim0007.cryptobench.discovery.adapter.ProviderProbe
import io.github.junekim0007.cryptobench.discovery.query.CaptureQuery
import io.github.junekim0007.cryptobench.discovery.trial.TrialRunner
import io.github.junekim0007.cryptobench.discovery.write.ProbeDirectory
import io.github.junekim0007.cryptobench.discovery.write.ProviderClassNameWriter
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File
import java.security.Security

/**
 * What probe.md assumes about the JCA, checked against the running JVM. A failure on a new Java
 * version means the JCA moved, not that the code broke. Says nothing about Android providers (#14).
 */
class JcaContractTest {

    @Test
    fun providersAreVisibleInPrecedenceOrder() {
        assertTrue("no provider registered a service", CAPTURE.providers.any { it.services.isNotEmpty() })
        assertTrue("precedence is not 1..n", CAPTURE.providers.map { it.precedence } == (1..CAPTURE.providers.size).toList())
        val serving = QUERY.whoServes("Cipher", "AES")
        assertTrue("whoServes is not in precedence order", serving.map { it.precedence } == serving.map { it.precedence }.sorted())
    }

    @Test
    fun theStaplesResolveAndInstantiateAndSomeDeclaredTransformationsDoNot() {
        listOf("Cipher" to "AES", "MessageDigest" to "SHA-256", "Mac" to "HmacSHA256", "Signature" to "SHA256withRSA", "KeyPairGenerator" to "RSA")
            .forEach { (type, algorithm) ->
                assertTrue("$type/$algorithm resolves to no provider", QUERY.whoServes(type, algorithm).isNotEmpty())
                assertTrue("$type is missing from the tree", QUERY.tree()[type].orEmpty().isNotEmpty())
            }
        val report = TrialRunner().run(CAPTURE, Security.getProviders())
        val aes = report.services.single { it.provider == "SunJCE" && it.type == "Cipher" && it.algorithm == "AES" }
        assertTrue("SunJCE AES does not instantiate: ${aes.outcome.error}", aes.outcome.instantiates)
        assertTrue("AES/CBC/PKCS5Padding is not tried", aes.transformations.any { it.name.equals("AES/CBC/PKCS5Padding", ignoreCase = true) && it.outcome.instantiates })
        assertTrue("no declared transformation failed; the trial has nothing to add over the capture", report.services.flatMap { it.transformations }.any { !it.outcome.instantiates })
    }

    /** Written out so a workflow can attach them and drift can be diffed instead of guessed. */
    @Test
    fun theFacadeWritesTheCaptureTheClassListAndTheTrial() {
        val discovery = Discovery(DIRECTORY)
        val run = discovery.probe(Security.getProviders())
        assertTrue("capture not written", run.captureFile.length() > 0 && run.captureFile.name.matches(Regex("probe_\\d{8}T\\d{6}Z\\.yaml")))
        assertTrue("class list not written", run.classesFile.length() > 0 && run.classesFile.name.matches(Regex("probe_classes_\\d{8}T\\d{6}Z\\.yaml")))
        assertTrue("the capture written differs from the capture returned", run.capture == CAPTURE.copy(capturedAtMillis = run.capture.capturedAtMillis))
        ProviderClassNameWriter(DIRECTORY).toDocument(CAPTURE).forEach { (provider, names) ->
            assertTrue("$provider lists a class twice or out of order", names == names.distinct().sorted())
        }
        val trial = discovery.trial(run.capture, Security.getProviders())
        assertTrue("unexpected name ${trial.name}", trial.name.matches(Regex("trial_\\d{8}T\\d{6}Z\\.yaml")))
    }

    private companion object {
        val CAPTURE = ProviderProbe().capture(Security.getProviders())
        val QUERY = CaptureQuery(CAPTURE)
        val DIRECTORY = ProbeDirectory(File(System.getProperty("capture.dir") ?: "build/capture"))
    }
}
