package io.github.junekim0007.cryptobench.document

import io.github.junekim0007.cryptobench.document.catalogue.FamilyCatalogue
import io.github.junekim0007.cryptobench.document.catalogue.Recipes
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

/** A recipe and an entry's rows at a build to a {class, arguments} tree; a builder, a keyRef, a missing value or recipe refused with guide_recipe_unbuildable. */
class RecipesTest {

    private val recipes = Recipes.parse(
        """
        schemaVersion: 1
        recipes:
          r.curve: {class: java.security.spec.ECGenParameterSpec, args: [{role: curve, kind: string}]}
          r.nested: {class: X, args: [{role: salt, kind: bytes}, {kind: constant, value: 7}, {kind: enum, value: A.B}, {kind: recipe, recipe: r.curve}]}
          r.builder: {builder: someBuilder}
          r.ref: {class: Y, args: [{role: publicKey, kind: keyRef}]}
        """.trimIndent(),
    )

    private val entry = FamilyCatalogue.parse(listOf(
        """
        family: f
        algorithms:
          Signature|S:
            required:
            - {name: curve, recipe: r.curve, value: c1, passedTo: keyGeneration}
            - {name: salt, recipe: r.nested, bytes: 8, passedTo: init}
            providers:
              P: {required.curve: {name: curve, recipe: r.curve, value: c2, passedTo: keyGeneration}}
        """.trimIndent(),
    )).entries.single()

    @Test
    fun aClassRecipeTakesEachRolesValueFromTheRowsAtTheBuild() {
        assertEquals(mapOf("class" to "java.security.spec.ECGenParameterSpec", "arguments" to listOf("c1")), recipes.tree("r.curve", entry, null))
        assertEquals(listOf("c2"), recipes.tree("r.curve", entry, "P")["arguments"])
        assertEquals(listOf("fresh(8)", 7, mapOf("field" to "A.B"), mapOf("class" to "java.security.spec.ECGenParameterSpec", "arguments" to listOf("c1"))),
            recipes.tree("r.nested", entry, null)["arguments"])
    }

    @Test
    fun aRecipeNoTreeCanMakeIsRefusedWithItsCode() {
        for (id in listOf("r.builder", "r.ref", "r.absent")) {
            val refused = assertThrows(Recipes.Unbuildable::class.java) { recipes.tree(id, entry, null) }
            assertEquals(Recipes.CODE, refused.message!!.substringBefore(':'))
        }
    }
}
