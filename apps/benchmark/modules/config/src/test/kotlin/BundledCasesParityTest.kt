package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.config.global.ProvidersDocument
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalSection
import io.github.junekim0007.cryptobench.files.RepositoryFiles
import org.junit.Assert.assertEquals
import org.junit.Test
import org.yaml.snakeyaml.LoaderOptions
import org.yaml.snakeyaml.Yaml
import org.yaml.snakeyaml.constructor.SafeConstructor
import java.io.File

// tests/contracts/documents/bundled-cases.json: the providers section read as GlobalDocument reads it, as Python's bundled.entries reads the same cases in test_authored.py.
class BundledCasesParityTest {

    @Test
    fun eachCaseIsRefusedWithItsCodeOrAccepted() {
        @Suppress("UNCHECKED_CAST")
        val cases = Yaml(SafeConstructor(LoaderOptions())).load<Map<String, Any>>(File(RepositoryFiles.documents, "bundled-cases.json").readText())["cases"] as List<Map<String, Any?>>
        val mismatches = cases.mapNotNull { case ->
            @Suppress("UNCHECKED_CAST")
            val code = try {
                optionalSection(case as Map<String, Any>, "providers")?.let { ProvidersDocument.parse(it, "providers") }
                null
            } catch (refused: IllegalArgumentException) {
                refused.message!!.substringBefore(':')
            }
            "${case["name"]}: expected ${case["code"]}, got $code".takeIf { code != case["code"] }
        }
        assertEquals(emptyList<String>(), mismatches)
    }
}
