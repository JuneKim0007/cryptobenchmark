package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.config.effective.OverrideResolver
import io.github.junekim0007.cryptobench.config.global.GlobalDocument
import io.github.junekim0007.cryptobench.config.inventory.dto.Inventory
import io.github.junekim0007.cryptobench.config.inventory.dto.InventoryEntry
import io.github.junekim0007.cryptobench.config.testset.TestSetDocument
import io.github.junekim0007.cryptobench.config.yaml.YamlFiles
import org.junit.Assert.assertEquals
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

    @Test
    fun sizedVariantsGetTheirOwnSizeAndTheSameFreshParameters() {
        assumeTrue("no config/ above ${File("").absolutePath}", root != null)
        val scope = YamlFiles().at(File(root, "config/testsets/scope.yaml"), TestSetDocument).read()
        val resolver = OverrideResolver(scope.overrides)
        fun resolve(name: String) = resolver.resolve(Inventory.Located("P", "Cipher", name, InventoryEntry(runs = true, keySizes = listOf(128))), null)
        val plain = resolve("AES/GCM/NoPadding")
        assertEquals(listOf(128, 192, 256), plain.keySizes)
        assertEquals(listOf(128), resolve("AES_128/GCM/NoPadding").keySizes)
        assertEquals(listOf(256), resolve("AES_256/GCM/NoPadding").keySizes)
        assertEquals(plain.parameters, resolve("AES_128/GCM/NoPadding").parameters)
        assertEquals(plain.parameters, resolve("AES_256/GCM/NoPadding").parameters)
        assertEquals(emptyList<String>(), resolve("AES_256/CBC/PKCS5Padding").providerDefaults)
    }
}
