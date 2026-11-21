package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.adapter.DiscoveryCapability
import io.github.junekim0007.cryptobench.preparation.record.PreparedFile
import io.github.junekim0007.cryptobench.preparation.report.SkipFile
import io.github.junekim0007.cryptobench.files.ContractsFolder
import io.github.junekim0007.cryptobench.files.StatedJson
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
import org.yaml.snakeyaml.LoaderOptions
import org.yaml.snakeyaml.Yaml
import org.yaml.snakeyaml.constructor.SafeConstructor
import java.io.File

/** The module runs on its own example files, with no other module on the classpath; -Dexamples.update also writes guide.json, the value tests/contracts/documents states for the example guide. */
class ExampleFilesTest {

    @get:Rule
    val output = TemporaryFolder()

    private val example = File("example")

    private val capability = DiscoveryCapability(
        File(example, "preparation_capture_example.yaml"),
        File(example, "preparation_trial_example.yaml"),
    )

    @Test
    fun theExampleEffectivePreparesEveryCaseTheGuideAllows() {
        val report = SkipFile(output.root)
        val record = PreparedFile(output.root)
        val run = Preparation(capability).prepareAll(File(example, "preparation_effective_example.yaml"), output.root)

        assertEquals(
            listOf(
                "[preparation] SunJCE Cipher AES/CBC/PKCS5Padding: guide_recipe_unbuildable: ['jca.gcmSpec', 'jca.ivSpec'] are several objects for one init",
                "[preparation] AndroidKeyStore Cipher RSA/ECB/PKCS1Padding: key_inside_provider: this provider keeps its own keys; its catalogue entry gives no keystore block to make one inside",
            ),
            run.skipped.map { it.toString() },
        )
        assertEquals(
            listOf(
                "Cipher_AES-GCM-NoPadding_DECRYPT_SunJCE_k128_i1024_WARM_p81667fe4",
                "Cipher_AES-GCM-NoPadding_DECRYPT_SunJCE_k256_i1024_WARM_p81667fe4",
                "Cipher_AES-GCM-NoPadding_ENCRYPT_SunJCE_k128_i1024_WARM_p81667fe4",
                "Cipher_AES-GCM-NoPadding_ENCRYPT_SunJCE_k256_i1024_WARM_p81667fe4",
                "Cipher_RSA-ECB-OAEPWithSHA-256AndMGF1Padding_DECRYPT_SunJCE_k2048_i32_WARM_p12833ef4",
                "Cipher_RSA-ECB-OAEPWithSHA-256AndMGF1Padding_ENCRYPT_SunJCE_k2048_i32_WARM_p12833ef4",
                "Mac_HmacSHA256_COMPUTE-MAC_SunJCE_i1024_WARM",
                "MessageDigest_SHA-256_DIGEST_SUN_i1024_WARM",
            ).flatMap { listOf("${it}_fixed", "${it}_notFixed") },
            run.cases.map { it.case.id }.sorted(),
        )
        assertExample("preparation_skipped_example.yaml", report.file)
        assertExample("preparation_prepared_example.yaml", record.file)
        if (System.getProperty("examples.update") != null) {
            StatedJson.write(File(ContractsFolder.documents, "guide.json"), Yaml(SafeConstructor(LoaderOptions())).load(File(example, "guide.yaml").readText()))
        }
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
