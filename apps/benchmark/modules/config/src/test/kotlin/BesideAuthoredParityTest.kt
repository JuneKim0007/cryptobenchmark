package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.files.Beside
import io.github.junekim0007.cryptobench.files.RepositoryFiles
import org.junit.Assert.assertEquals
import org.junit.Test
import org.yaml.snakeyaml.LoaderOptions
import org.yaml.snakeyaml.Yaml
import org.yaml.snakeyaml.constructor.SafeConstructor
import java.io.File

/** tests/contracts/documents/beside-authored.json: the test-set path rule, as Python's paths.beside reads the same cases in test_authored.py. */
class BesideAuthoredParityTest {

    @Test
    fun eachTestSetValueIsTheStatedPath() {
        @Suppress("UNCHECKED_CAST")
        val stated = Yaml(SafeConstructor(LoaderOptions())).load<Map<String, Any>>(File(RepositoryFiles.documents, "beside-authored.json").readText())
        val settingsFile = File(stated["settingsFile"] as String)
        @Suppress("UNCHECKED_CAST")
        for (case in stated["cases"] as List<Map<String, String>>) {
            assertEquals(case["value"], case["path"], Beside.authored(settingsFile, case.getValue("value")).path)
        }
    }
}
