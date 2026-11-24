package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.config.effective.EffectiveBuilder
import io.github.junekim0007.cryptobench.config.global.GlobalDocument
import io.github.junekim0007.cryptobench.config.inventory.InventoryBuilder
import io.github.junekim0007.cryptobench.config.testset.TestSetDocument
import io.github.junekim0007.cryptobench.document.DocumentFields
import io.github.junekim0007.cryptobench.document.YamlCodec
import io.github.junekim0007.cryptobench.document.names.AlgorithmNames
import io.github.junekim0007.cryptobench.document.names.NameLayers
import io.github.junekim0007.cryptobench.document.names.dto.Canonical
import io.github.junekim0007.cryptobench.document.names.CaptureSpellings
import io.github.junekim0007.cryptobench.files.RepositoryFiles
import org.junit.Assert.assertEquals
import org.junit.Assert.assertSame
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

/** tests/contracts/catalogue/name-layers-cases.yaml as Python's name_layers reads it, and config's rules matching through the merged names. */
class CaptureLayerTest {

    private val codec = YamlCodec.DOCUMENT
    private val cases = codec.load(File(RepositoryFiles.catalogue, "name-layers-cases.yaml").readText())

    @Test
    fun theSharedCasesMergeAlike() {
        val rows = DocumentFields.sections(cases, "capture")
        fun layered(rows: List<Map<String, Any>>) = NameLayers.merged(AlgorithmNames.catalog, CaptureSpellings(rows.groupBy({ DocumentFields.string(it, "provider") }) {
            CaptureSpellings.Service(DocumentFields.string(it, "type"), DocumentFields.string(it, "algorithm"), DocumentFields.strings(it, "aliases"))
        }))
        val layered = layered(rows)
        val conflicts = DocumentFields.sections(cases, "conflicts").associate { (DocumentFields.string(it, "type") to DocumentFields.string(it, "alias")) to DocumentFields.string(it, "why") }
        assertEquals(conflicts, layered.conflicts)
        assertEquals(conflicts, layered(rows.reversed()).conflicts)
        for (case in DocumentFields.sections(cases, "lookups")) {
            val type = DocumentFields.string(case, "type")
            val name = DocumentFields.string(case, "name")
            if ("refused" in case) {
                assertEquals(case["refused"], assertThrows(IllegalArgumentException::class.java) { layered.canonical(type, name) }.message)
            } else {
                val want = DocumentFields.section(case, "canonical")
                assertEquals(name, Canonical(want["name"] as String, want["keySize"] as Int?, want["known"] as Boolean), layered.canonical(type, name))
            }
            val key = case["key"] as List<*>
            assertEquals(name, key[0] to key[1], layered.keyOrSpelling(type, name))
        }
    }

    @Test
    fun noCaptureIsTheBase() {
        assertSame(AlgorithmNames.catalog, NameLayers.merged(AlgorithmNames.catalog, null))
    }

    private val inventory = InventoryBuilder().build(
        Fixtures.capture(Fixtures.CAPTURE
            .replace("{name: SUN, version: '25', precedence: 1, origin: platform, services: []}",
                "{name: SUN, version: '25', precedence: 1, origin: platform, services: [{type: MessageDigest, algorithm: SHA-256, className: x, aliases: [SHA-512]}]}")
            .replace("{name: SunJCE, version: '25', precedence: 2, origin: platform, services: []}",
                "{name: SunJCE, version: '25', precedence: 2, origin: platform, services: [{type: Cipher, algorithm: AES, className: x, aliases: [VENDORAES, VENDORX]}, " +
                    "{type: Cipher, algorithm: RSA, className: x, aliases: [VENDORX]}]}")),
        Fixtures.trial(), InventoryBuilder.Files("probe_x.yaml", "trial_x.yaml"))

    private fun build(include: String) = EffectiveBuilder().build(
        GlobalDocument.parse(codec.load(Fixtures.seeded("schemaVersion: 1\nselection: {testSet: t.yaml}\n"))),
        TestSetDocument.parse(codec.load("schemaVersion: 1\ndescription: d\ninclude:\n- $include\n")), inventory,
        EffectiveBuilder.Files("global.yaml", "t.yaml", "inventory.yaml"))

    @Test
    fun aRuleNamingADeviceOnlyAliasMatchesItsService() {
        assertEquals(listOf("AES"), build("{type: Cipher, name: vendoraes}").providers.getValue("SunJCE").getValue("Cipher").keys.toList())
    }

    @Test
    fun aRuleNamingAnAliasTwoServicesMeanApartIsRefused() {
        assertEquals("name_conflict: Cipher VENDORX: SunJCE says AES, SunJCE says RSA",
            assertThrows(IllegalArgumentException::class.java) { build("{name: VENDORX}") }.message)
    }

    @Test
    fun aRuleNamingANamesFileSpellingAProviderAliasesElsewhereKeepsTheNamesFileAndWarns() {
        val effective = build("{type: MessageDigest, name: SHA-512}\n- {type: MessageDigest, name: SHA-256}")
        assertEquals(listOf("SHA-256"), effective.providers.getValue("SUN").getValue("MessageDigest").keys.toList())
        assertTrue(effective.warnings.toString(), "alias_conflict: MessageDigest|SHA-512: catalog says SHA-512; SUN says SHA-256" in effective.warnings)
    }
}
