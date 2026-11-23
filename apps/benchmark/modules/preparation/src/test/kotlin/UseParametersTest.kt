package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.document.catalogue.FamilyCatalogue
import io.github.junekim0007.cryptobench.document.catalogue.Recipes
import io.github.junekim0007.cryptobench.preparation.peer.UseParameters
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertThrows
import org.junit.Test
import java.security.spec.ECGenParameterSpec

/** A key use's init rows on the producer's build, else the consumer's, made and bound; none without rows; several recipes or one not made refused with its code. */
class UseParametersTest {

    private val recipes = Recipes.parse(
        """
        schemaVersion: 1
        recipes:
          r.curve: {class: java.security.spec.ECGenParameterSpec, args: [{role: curve, kind: string}]}
          r.group: {builder: namedGroupSpec}
        """.trimIndent(),
    )

    private fun entry(base: String, providers: String = "{}") = FamilyCatalogue.parse(listOf(
        "family: f\nalgorithms:\n  Signature|S:\n    required: $base\n    providers: $providers\n",
    )).entries.single()

    private val parameters = UseParameters(recipes)

    @Test
    fun theProducersRowsThenTheConsumersAreBound() {
        val onQ = entry("[]", "{Q: {required.curve: {name: curve, recipe: r.curve, value: secp256r1, passedTo: init}}}")
        val bound = parameters.of(onQ, listOf("P", "Q"))!!
        assertEquals("secp256r1", (bound.next() as ECGenParameterSpec).name)
        val both = entry("[{name: curve, recipe: r.curve, value: secp384r1, passedTo: init}]", "{Q: {required.curve: {name: curve, recipe: r.curve, value: secp256r1, passedTo: init}}}")
        assertEquals("secp384r1", (parameters.of(both, listOf("P", "Q"))!!.next() as ECGenParameterSpec).name)
        assertNull(parameters.of(entry("[{name: curve, recipe: r.curve, value: x, passedTo: keyGeneration}]"), listOf("P", "Q")))
    }

    @Test
    fun aRecipeNotMadeOrSeveralAreRefusedWithTheCode() {
        val builder = assertThrows(Recipes.Unbuildable::class.java) { parameters.of(entry("[{name: group, recipe: r.group, value: g, passedTo: init}]"), listOf("P")) }
        assertEquals("${Recipes.CODE}: r.group is not a constructor", builder.message)
        val several = assertThrows(Recipes.Unbuildable::class.java) {
            parameters.of(entry("[{name: curve, recipe: r.curve, value: a, passedTo: init}, {name: group, recipe: r.group, value: b, passedTo: init}]"), listOf("P"))
        }
        assertEquals("${Recipes.CODE}: [r.curve, r.group] are several objects for one init", several.message)
    }
}
