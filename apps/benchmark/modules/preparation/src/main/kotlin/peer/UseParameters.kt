package io.github.junekim0007.cryptobench.preparation.peer

import io.github.junekim0007.cryptobench.document.catalogue.FamilyCatalogue
import io.github.junekim0007.cryptobench.document.catalogue.Recipes
import io.github.junekim0007.cryptobench.jca.bind.BoundParameters
import io.github.junekim0007.cryptobench.jca.bind.ParameterBinder

/** A key use's parameters: its required rows passed to init on the first build that has any (the producer's, then the consumer's), their one recipe made by document's Recipes and bound by jca's ParameterBinder, with the recipe and build they came from; none without such a row, a coded refusal for a recipe not made or bound. */
internal class UseParameters(private val recipes: Recipes = Recipes.bundled, private val binder: ParameterBinder = ParameterBinder()) {

    class Bound(val parameters: BoundParameters, val recipe: String, val build: String?) {
        override fun toString() = "$INIT $recipe of ${build ?: "the base entry"}"
    }

    fun of(entry: FamilyCatalogue.Entry, builds: List<String?>): Bound? {
        val (build, id) = builds.firstNotNullOfOrNull { build -> recipes.one(entry, build, INIT)?.let { build to it } } ?: return null
        return Bound(binder.bind(recipes.tree(id, entry, build), "$INIT.$id"), id, build)
    }

    private companion object {
        const val INIT = "init"
    }
}
