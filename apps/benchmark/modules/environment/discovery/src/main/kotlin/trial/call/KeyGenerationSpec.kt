package io.github.junekim0007.cryptobench.discovery.trial.call

import io.github.junekim0007.cryptobench.document.catalogue.FamilyCatalogue
import io.github.junekim0007.cryptobench.document.catalogue.Recipes
import io.github.junekim0007.cryptobench.jca.bind.ParameterBinder
import io.github.junekim0007.cryptobench.jca.failure.Attempt
import java.security.spec.AlgorithmParameterSpec

/** A catalogued entry's key-generation spec at a build: its `passedTo: keyGeneration` rows' one recipe, made by document's Recipes and bound by jca's ParameterBinder; [Refused] carries the coded reason a recipe was not built or bound. */
internal sealed class KeyGenerationSpec {

    object None : KeyGenerationSpec()

    class Built(val label: String, val spec: AlgorithmParameterSpec) : KeyGenerationSpec()

    class Refused(val recipe: String, val reason: String) : KeyGenerationSpec()

    companion object {

        private const val KEY_GENERATION = "keyGeneration"

        fun of(entry: FamilyCatalogue.Entry, build: String?, recipes: Recipes = Recipes.bundled, binder: ParameterBinder = ParameterBinder()): KeyGenerationSpec {
            val id = Attempt.of { recipes.one(entry, build, KEY_GENERATION) }
                .getOrElse { return Refused((it as? Recipes.Unbuildable)?.recipes.orEmpty().joinToString(), it.message ?: it.javaClass.name) } ?: return None
            return Attempt.of { recipes.tree(id, entry, build).let { tree -> Built("$id${tree["arguments"]}", binder.bind(tree, "$KEY_GENERATION.$id").next()) } }
                .getOrElse { Refused(id, it.message ?: it.javaClass.name) }
        }
    }
}
