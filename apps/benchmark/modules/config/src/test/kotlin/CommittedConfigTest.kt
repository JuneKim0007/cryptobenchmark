package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.config.global.GlobalDocument
import io.github.junekim0007.cryptobench.config.testset.TestSetDocument
import io.github.junekim0007.cryptobench.config.yaml.YamlFiles
import org.junit.Assume.assumeTrue
import org.junit.Test
import java.io.File

/** The files committed under config/ still parse. They live outside the module, so the module-isolation build, which runs from the module directory, skips this. */
class CommittedConfigTest {

    private val root = generateSequence(File("").absoluteFile) { it.parentFile }.firstOrNull { File(it, "config/global.yaml").exists() }

    @Test
    fun theCommittedConfigParses() {
        assumeTrue("no config/ above ${File("").absolutePath}", root != null)
        val files = YamlFiles()
        File(root, "config").listFiles { file -> file.name.startsWith("global") && file.name.endsWith(".yaml") }!!.forEach { file ->
            files.at(file, GlobalDocument).read()
        }
        File(root, "config/testsets").listFiles { file -> file.name.endsWith(".yaml") }!!.forEach { file ->
            files.at(file, TestSetDocument).read()
        }
    }
}
