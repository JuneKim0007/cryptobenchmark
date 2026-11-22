package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.config.global.ProvidersDocument
import io.github.junekim0007.cryptobench.files.RepositoryFiles
import org.junit.Assert.assertEquals
import org.junit.Test
import org.yaml.snakeyaml.LoaderOptions
import org.yaml.snakeyaml.Yaml
import org.yaml.snakeyaml.constructor.SafeConstructor
import java.io.File

// tests/contracts/documents/bundled-cases.json: the providers.bundled rule, as Python's bundled.entries reads the same cases in test_authored.py.
class BundledCasesParityTest {

    @Test
    fun eachCaseIsRefusedWithItsCodeOrAccepted() {
        @Suppress("UNCHECKED_CAST")
        val cases = Yaml(SafeConstructor(LoaderOptions())).load<Map<String, Any>>(File(RepositoryFiles.documents, "bundled-cases.json").readText())["cases"] as List<Map<String, Any?>>
        for (case in cases) {
            @Suppress("UNCHECKED_CAST")
            val code = try {
                ProvidersDocument.parse(case["providers"] as Map<String, Any>, "providers")
                null
            } catch (refused: IllegalArgumentException) {
                refused.message!!.substringBefore(':')
            }
            assertEquals(case["name"] as String, case["code"], code)
        }
    }
}
