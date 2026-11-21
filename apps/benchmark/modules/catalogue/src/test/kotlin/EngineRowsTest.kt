package io.github.junekim0007.cryptobench.catalogue

import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

class EngineRowsTest {

    private fun rows(engines: Map<String, Any>) = EngineRows(mapOf("schemaVersion" to 1, "engines" to engines))

    private val catalogue = rows(mapOf(
        "Mac" to mapOf("fixed" to "operation"),
        "KeyGenerator" to mapOf("variants" to listOf("fixed", "secure"), "generates" to "secretKey"),
        "KeyPairGenerator" to mapOf("variants" to listOf("fixed", "secure"), "generates" to "keyPair"),
    ))

    @Test
    fun aRowAppliesItsVariantsOrFixedAndNotFixedAndAMissingTypeAppliesNone() {
        assertEquals(listOf("fixed", "notFixed"), catalogue.applicable("mac"))
        assertEquals(listOf("fixed", "secure"), catalogue.applicable("KeyGenerator"))
        assertEquals(emptyList<String>(), catalogue.applicable("KEM"))
        assertEquals(null, catalogue.row("KEM"))
        assertEquals(listOf("KeyGenerator", "KeyPairGenerator"), catalogue.taking("secure"))
        assertEquals("not_in_catalogue: KEM has no row in setup-catalog.yaml", EngineRows.notInCatalogue("KEM"))
    }

    @Test
    fun invalidVariantsAreRefused() {
        for (bad in listOf(emptyList<String>(), listOf("fast"), listOf("fixed", "fixed"))) {
            val refused = assertThrows(IllegalArgumentException::class.java) { rows(mapOf("Mac" to mapOf("variants" to bad))).applicable("Mac") }
            assertEquals("invalid: setup-catalog.yaml engines.Mac.variants $bad, distinct names of [fixed, notFixed, secure]", refused.message)
        }
    }

    /** The generator of each key kind is the one row naming it; none or two is refused, never guessed. */
    @Test
    fun eachKeyKindHasExactlyOneGeneratorRow() {
        assertEquals(listOf("KeyGenerator", "KeyPairGenerator"), catalogue.generators)
        assertEquals("KeyGenerator", catalogue.generator(EngineRows.SECRET_KEY))
        assertEquals("KeyPairGenerator", catalogue.generator(EngineRows.KEY_PAIR))
        for ((types, named) in listOf(emptyList<String>() to "no type", listOf("A", "B") to "[A, B]")) {
            val refused = assertThrows(IllegalArgumentException::class.java) {
                rows(types.associateWith { mapOf("generates" to "keyPair") }).generator(EngineRows.KEY_PAIR)
            }
            assertEquals("invalid: setup-catalog.yaml engines name $named with generates: keyPair, exactly one wanted", refused.message)
        }
    }

    @Test
    fun aDocumentWithoutEnginesIsRefused() {
        assertEquals("missing_field: setup-catalog.yaml engines", assertThrows(IllegalArgumentException::class.java) { EngineRows(mapOf("schemaVersion" to 1)) }.message)
    }
}
