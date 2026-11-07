package io.github.junekim0007.cryptobench.preparation.key.generate

import io.github.junekim0007.cryptobench.preparation.key.plan.KeyRecipe
import io.github.junekim0007.cryptobench.preparation.parameter.bind.ParameterBinder
import java.security.KeyPairGenerator
import java.security.SecureRandom
import java.security.spec.AlgorithmParameterSpec
import javax.crypto.KeyGenerator

class KeyMaterialGenerator(private val binder: ParameterBinder = ParameterBinder()) {

    private val random = SecureRandom()

    fun generate(recipe: KeyRecipe): KeyMaterial = when (recipe) {
        KeyRecipe.None -> KeyMaterial.None
        is KeyRecipe.Secret -> KeyMaterial.Secret(secret(recipe))
        is KeyRecipe.Pair -> KeyMaterial.Pairs(List(recipe.count) { pair(recipe) })
        is KeyRecipe.Unavailable -> throw IllegalArgumentException("unavailable_recipe: ${recipe.reason}")
    }

    private fun secret(recipe: KeyRecipe.Secret) =
        KeyGenerator.getInstance(recipe.algorithm, recipe.provider)
            .also { KeyInitializer.initialize(it, recipe.keySize, spec(recipe.parameters), random) }
            .generateKey()

    private fun pair(recipe: KeyRecipe.Pair) =
        KeyPairGenerator.getInstance(recipe.algorithm, recipe.provider)
            .also { KeyInitializer.initialize(it, recipe.keySize, spec(recipe.parameters), random) }
            .generateKeyPair()

    private fun spec(parameters: Map<String, Any>): AlgorithmParameterSpec? =
        if (parameters.isEmpty()) null else binder.bind(parameters, "key").next()
}
