package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.document.DocumentFields
import io.github.junekim0007.cryptobench.document.YamlCodec
import io.github.junekim0007.cryptobench.document.catalogue.FamilyCatalogue
import io.github.junekim0007.cryptobench.files.RepositoryFiles
import org.junit.Assert.assertEquals
import org.junit.Test
import java.io.File

/** tests/contracts/catalogue/key-types.yaml: each entry's key.type as its provider's build on the platform sees it, the rows Python's provider-agreement rule reads alike. */
class KeyTypeContractTest {

    @Test
    fun eachEntryTakesTheFixturesKeyType() {
        val catalogue = FamilyCatalogue.bundled(FamilyCatalogue.KEYED + FamilyCatalogue.GENERATORS)
        val cases = DocumentFields.sections(YamlCodec.DOCUMENT.load(File(RepositoryFiles.catalogue, "key-types.yaml").readText()), "cases")
        val found = cases.map { c ->
            val entry = catalogue.of(DocumentFields.string(c, "type"), DocumentFields.string(c, "name"))
            entry?.keyType(catalogue.build(DocumentFields.string(c, "provider"), DocumentFields.string(c, "platform")))
        }
        assertEquals(cases.map { DocumentFields.string(it, "keyType") }, found)
    }
}
