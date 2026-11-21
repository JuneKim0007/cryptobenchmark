package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.config.global.GlobalDocument
import io.github.junekim0007.cryptobench.config.testset.TestSetDocument
import io.github.junekim0007.cryptobench.document.versioned.YamlFiles
import io.github.junekim0007.cryptobench.files.RepositoryFiles
import org.junit.Test
import java.io.File

/** The files committed under config/benchmark/ and the runner tests' config fixtures still parse. */
class CommittedConfigTest {

    @Test
    fun theCommittedConfigParses() {
        val files = YamlFiles()
        listOf(RepositoryFiles.benchmarkConfig, File(RepositoryFiles.root, "apps/benchmark-runner/tests/fixtures/config")).forEach { folder ->
            folder.listFiles { file -> file.name.startsWith("global") && file.name.endsWith(".yaml") }!!.forEach { file ->
                files.at(file, GlobalDocument).read()
            }
            File(folder, "testsets").listFiles { file -> file.name.endsWith(".yaml") }!!.forEach { file ->
                files.at(file, TestSetDocument).read()
            }
        }
    }
}
