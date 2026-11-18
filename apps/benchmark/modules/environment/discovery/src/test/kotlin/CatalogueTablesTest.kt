package io.github.junekim0007.cryptobench.discovery.trial.call

import io.github.junekim0007.cryptobench.discovery.trial.requirement.RequirementCalls
import io.github.junekim0007.cryptobench.document.DocumentFields
import io.github.junekim0007.cryptobench.document.YamlCodec
import org.junit.Assert.assertEquals
import org.junit.Test
import java.io.File

/** Every setup-catalog type has its row in discovery's type-keyed tables: DefaultCalls, RequirementCalls and KeyNames. */
class CatalogueTablesTest {

    // discovery's classpath has no guide files: the catalogue is read from the checkout
    private val types: Set<String> = run {
        val file = generateSequence(File("").absoluteFile) { it.parentFile }.map { File(it, "algorithms/setup-catalog.yaml") }.first { it.isFile }
        DocumentFields.section(YamlCodec.DOCUMENT.load(file.readText()), "engines").keys
    }

    @Test
    fun everyCatalogueTypeHasADefaultCallAndARequirementCall() {
        assertEquals(emptyList<String>(), types.filter { DefaultCalls.of(it) == null })
        assertEquals(emptyList<String>(), types.filter { RequirementCalls.of(it) == null })
    }

    @Test
    fun todayKeyNamesHasRowsForThreeCatalogueTypesAndPassesTheOthersThrough() {
        val probes = listOf("AES_128/GCM/NoPadding", "SHA256withECDSA", "ECDH")
        val ruled = types.filter { type -> probes.any { KeyNames.candidates(type, it) != listOf(it to null) } }
        assertEquals(listOf("Signature", "KeyAgreement", "Cipher"), ruled)
    }
}
