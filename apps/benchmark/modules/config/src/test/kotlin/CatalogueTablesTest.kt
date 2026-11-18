package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.document.DocumentFields
import io.github.junekim0007.cryptobench.document.YamlCodec
import org.junit.Assert.assertEquals
import org.junit.Test

/** Every setup-catalog type has its section in algorithm-names.yaml. */
class CatalogueTablesTest {

    private fun keys(resource: String, section: String) =
        DocumentFields.section(YamlCodec.DOCUMENT.load(javaClass.getResource(resource)!!.readText()), section).keys

    @Test
    fun everyCatalogueTypeHasCanonicalNames() {
        assertEquals(emptySet<String>(), keys("/setup-catalog.yaml", "engines") - keys("/algorithm-names.yaml", "names"))
    }
}
