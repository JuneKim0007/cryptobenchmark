package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.adapter.DiscoveryCapability
import io.github.junekim0007.cryptobench.preparation.report.SkipFile
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
import java.io.File

/** The module runs on its own example files, with no other module on the classpath. */
class ExampleFilesTest {

    @get:Rule
    val output = TemporaryFolder()

    private val example = File("example")

    private val capability = DiscoveryCapability(
        File(example, "preparation_capture_example.yaml"),
        File(example, "preparation_trial_example.yaml"),
    )

    @Test
    fun theExampleEffectivePreparesEveryCase() {
        val report = SkipFile(output.root)
        val run = Preparation(capability, report).prepare(File(example, "preparation_effective_example.yaml"))

        assertEquals(emptyList<String>(), run.skipped.map { it.toString() })
        assertEquals(
            listOf(
                "Cipher_AES-GCM-NoPadding_DECRYPT_SunJCE_k128_i1024_WARM_p81667fe4",
                "Cipher_AES-GCM-NoPadding_DECRYPT_SunJCE_k256_i1024_WARM_p81667fe4",
                "Cipher_AES-GCM-NoPadding_ENCRYPT_SunJCE_k128_i1024_WARM_p81667fe4",
                "Cipher_AES-GCM-NoPadding_ENCRYPT_SunJCE_k256_i1024_WARM_p81667fe4",
                "Mac_HmacSHA256_COMPUTE-MAC_SunJCE_i1024_WARM",
                "MessageDigest_SHA-256_DIGEST_SUN_i1024_WARM",
            ),
            run.cases.map { it.case.id }.sorted(),
        )
        assertExample("preparation_skipped_example.yaml", report.file)
    }

    @Test
    fun theExampleDeviceIsReadFromYamlAlone() {
        assertEquals(listOf("SUN", "SunJCE"), capability.providers())
    }

    private fun assertExample(name: String, written: File) {
        val committed = File(example, name)
        if (System.getProperty("examples.update") != null) {
            written.copyTo(committed, overwrite = true)
            return
        }
        assertEquals("$name is not what this build writes; rerun with -Dexamples.update", committed.readText(), written.readText())
    }
}
