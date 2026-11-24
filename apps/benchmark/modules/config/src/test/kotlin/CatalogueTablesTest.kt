package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.document.DocumentFields
import io.github.junekim0007.cryptobench.document.YamlCodec
import io.github.junekim0007.cryptobench.document.names.AlgorithmNames
import org.junit.Assert.assertEquals
import org.junit.Test

/** Every setup-catalog type has its section in name-index.yaml. */
class CatalogueTablesTest {

    private fun keys(resource: String, section: String, beside: Class<*> = javaClass) =
        DocumentFields.section(YamlCodec.DOCUMENT.load(beside.getResource(resource)!!.readText()), section).keys

    @Test
    fun everyCatalogueTypeHasCanonicalNames() {
        assertEquals(emptySet<String>(), keys("/setup-catalog.yaml", "engines") - keys(AlgorithmNames.FILE, AlgorithmNames.SPELLINGS, AlgorithmNames::class.java))
    }
}
