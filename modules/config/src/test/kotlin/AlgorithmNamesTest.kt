package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.config.inventory.dto.Inventory
import io.github.junekim0007.cryptobench.config.inventory.dto.InventoryEntry
import io.github.junekim0007.cryptobench.config.inventory.dto.InventorySource
import io.github.junekim0007.cryptobench.config.names.AlgorithmNames
import io.github.junekim0007.cryptobench.config.names.dto.Canonical
import io.github.junekim0007.cryptobench.config.testset.dto.Rule
import io.github.junekim0007.cryptobench.config.yaml.YamlCodec
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File
import java.security.Security

class AlgorithmNamesTest {

    private val names = AlgorithmNames.catalog

    @Suppress("UNCHECKED_CAST")
    @Test
    fun theCasesSharedWithPerfRepairResolveAlike() {
        val path = "apps/perf-repair/tests/fixtures/algorithm-names-cases.yaml"
        val root = generateSequence(File("").absoluteFile) { it.parentFile }.firstOrNull { File(it, path).exists() }
            ?: error("no $path above ${File("").absolutePath}")
        val cases = YamlCodec().load(File(root, path).readText())["cases"] as List<Map<String, Any?>>
        assertTrue(cases.size > 20)
        for (case in cases) {
            val expected = Canonical(case["canonical"] as String, case["keySize"] as Int?, case["known"] as Boolean)
            assertEquals("${case["type"]} ${case["name"]}", expected, names.canonical(case["type"] as String, case["name"] as String))
        }
    }

    @Test
    fun noTwoServicesOfOneRunningProviderShareACanonicalName() {
        val clashes = Security.getProviders().flatMap { provider ->
            provider.services.groupBy { it.type to names.key(it.type, it.algorithm) }
                .filterValues { it.size > 1 }
                .map { (key, same) -> "${provider.name}.${key.first} ${same.map { it.algorithm }}" }
        }
        assertEquals(emptyList<String>(), clashes)
    }

    @Suppress("UNCHECKED_CAST")
    @Test
    fun everyCataloguedSpellingResolvesToItsCanonicalName() {
        val text = AlgorithmNames::class.java.getResource(AlgorithmNames.RESOURCE)!!.readText()
        val catalog = YamlCodec().load(text)["names"] as Map<String, Map<String, List<String>?>>
        for ((type, spellings) in catalog) {
            for ((canonical, aliases) in spellings) {
                for (spelling in listOf(canonical, canonical.lowercase()) + aliases.orEmpty()) {
                    assertEquals("$type $spelling", Canonical(canonical), names.canonical(type, spelling))
                }
            }
        }
    }

    @Test
    fun aSpellingUnderTwoCanonicalNamesIsRefused() {
        val document = YamlCodec().load("schemaVersion: 1\nnames:\n  MessageDigest:\n    SHA-1: [SHA]\n    SHA-0: [sha]\n")
        val error = assertThrows(IllegalArgumentException::class.java) { AlgorithmNames.parse(document) }
        assertTrue(error.message!!.startsWith("names_catalog_duplicate:"))
    }

    @Test
    fun anInventoryRefusesTwoSpellingsOfOneNameButKeepsKeySizesApart() {
        val source = InventorySource("capture.yaml", "trial.yaml", emptyMap())
        fun inventory(vararg names: String) = Inventory(source, mapOf("P" to mapOf("MessageDigest" to names.associateWith { InventoryEntry(runs = true) })))
        val error = assertThrows(IllegalArgumentException::class.java) { inventory("SHA-1", "SHA") }
        assertEquals("duplicate_name: P.MessageDigest [SHA-1, SHA]", error.message)
        Inventory(source, mapOf("P" to mapOf("Cipher" to listOf("AES/GCM/NoPadding", "AES_128/GCM/NoPadding").associateWith { InventoryEntry(runs = true) })))
    }

    @Test
    fun aRuleMatchesEverySpellingOfItsName() {
        assertTrue(Rule(type = "MessageDigest", name = "SHA256").matches("SUN", "MessageDigest", "SHA-256"))
        assertTrue(Rule(name = "aes/cbc/pkcs7padding").matches("P", "Cipher", "AES/CBC/PKCS5PADDING"))
        assertFalse(Rule(name = "SHA256").matches("P", "MessageDigest", "SHA-512"))
    }

    @Test
    fun patternsMatchTheGivenOrTheCanonicalSpelling() {
        assertTrue(names.matches("MessageDigest", "sha", "SHA-1"))
        assertTrue(names.matches("MessageDigest", "SHA-*", "SHA256"))
        assertTrue(names.matches("Cipher", "*/GCM/*", "AES_128/GCM/NoPadding"))
        assertFalse(names.matches("Cipher", "AES/GCM/NoPadding", "AES_128/GCM/NoPadding"))
    }
}
