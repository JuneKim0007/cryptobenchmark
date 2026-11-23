package io.github.junekim0007.cryptobench.preparation.peer

import io.github.junekim0007.cryptobench.document.catalogue.FamilyCatalogue
import io.github.junekim0007.cryptobench.document.catalogue.Recipes
import io.github.junekim0007.cryptobench.jca.bind.BoundParameters
import io.github.junekim0007.cryptobench.jca.bind.ParameterBinder

/** A key use's parameters: its required rows passed to init on the first build that has any (the producer's, then the consumer's), their one recipe made by document's Recipes and bound by jca's ParameterBinder; none without such a row, a coded refusal for a recipe not made or bound. */
internal class UseParameters(private val recipes: Recipes = Recipes.bundled, private val binder: ParameterBinder = ParameterBinder()) {

    fun of(entry: FamilyCatalogue.Entry, builds: List<String?>): BoundParameters? {
        val (build, ids) = builds.map { it to recipes.ids(entry, it, INIT) }.firstOrNull { it.second.isNotEmpty() } ?: return null
        val id = ids.singleOrNull() ?: throw Recipes.Unbuildable("$ids are several objects for one $INIT")
        return binder.bind(recipes.tree(id, entry, build), "$INIT.$id")
    }

    private companion object {
        const val INIT = "init"
    }
}
