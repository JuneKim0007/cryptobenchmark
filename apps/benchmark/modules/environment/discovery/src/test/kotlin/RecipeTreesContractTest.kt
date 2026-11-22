package io.github.junekim0007.cryptobench.discovery

import io.github.junekim0007.cryptobench.document.DocumentFields
import io.github.junekim0007.cryptobench.document.YamlCodec
import io.github.junekim0007.cryptobench.document.catalogue.FamilyCatalogue
import io.github.junekim0007.cryptobench.document.catalogue.Recipes
import io.github.junekim0007.cryptobench.files.RepositoryFiles
import org.junit.Assert.assertEquals
import org.junit.Test
import java.io.File

/** tests/contracts/catalogue/recipe-trees.yaml: document's Recipes makes each case's tree, or refuses it with guide_recipe_unbuildable, as Python's guide_items.parameter_tree does in test_recipe_trees.py. */
class RecipeTreesContractTest {

    @Test
    fun eachRecipeRowMakesTheFixturesTreeOrItsRefusal() {
        val catalogue = FamilyCatalogue.bundled(FamilyCatalogue.KEYED + FamilyCatalogue.GENERATORS)
        val cases = DocumentFields.sections(YamlCodec.DOCUMENT.load(File(RepositoryFiles.catalogue, "recipe-trees.yaml").readText()), "cases")
        val expected = cases.map { it["tree"] ?: it["refused"] }
        val found = cases.map { case ->
            val id = DocumentFields.string(case, "id")
            val entry = catalogue.of(id.substringBefore('|'), id.substringAfter('|')) ?: error("no entry $id")
            try {
                Recipes.bundled.tree(DocumentFields.string(case, "recipe"), entry, case["build"] as String?)
            } catch (refused: Recipes.Unbuildable) {
                refused.message!!.substringBefore(':')
            }
        }
        assertEquals(cases.size, expected.size)
        cases.indices.filter { expected[it] != found[it] }.take(5).forEach { assertEquals("case $it ${cases[it]}", expected[it], found[it]) }
    }
}
