package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.config.global.GlobalDocument
import io.github.junekim0007.cryptobench.config.testset.TestSetDocument
import io.github.junekim0007.cryptobench.config.yaml.YamlFiles
import org.junit.Assert.assertEquals
import org.junit.Assume.assumeTrue
import org.junit.Test
import java.io.File

/** The files committed under config/ still parse. They live outside the module, so the module-isolation build, which runs from the module directory, skips this. */
class CommittedConfigTest {

    @Test
    fun theCommittedConfigParses() {
        val root = generateSequence(File("").absoluteFile) { it.parentFile }.firstOrNull { File(it, "config/global.yaml").exists() }
        assumeTrue("no config/ above ${File("").absolutePath}", root != null)
        val files = YamlFiles()
        val committed = files.at(File(root, "config/global.yaml"), GlobalDocument).read()
        File(root, "config/testsets").listFiles { file -> file.name.endsWith(".yaml") }!!.forEach { file ->
            files.at(file, TestSetDocument).read()
        }
        assertEquals("testsets/scope.yaml", committed.selection.testSet)
        // the reference lists every key, so a key renamed in the schema fails here instead of misleading a reader
        val reference = files.at(File(root, "config/global.reference.yaml"), GlobalDocument).read()
        assertEquals("testsets/scope.yaml", reference.selection.testSet)
        assertEquals(50, reference.run.harness.iterations)
    }
}
