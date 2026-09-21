package io.github.junekim0007.cryptobench.benchmark.preparation.key.generate

import io.github.junekim0007.cryptobench.benchmark.preparation.key.plan.KeyRecipe
import java.security.KeyPairGenerator
import java.security.SecureRandom
import javax.crypto.KeyGenerator

/** Recipe → key material. The only key code that calls the JCA; always outside the timed region. */
class KeyMaterialGenerator(
    private val random: SecureRandom = SecureRandom(),
    private val initializers: Map<String, KeyInitializer> = emptyMap(),
    private val fallback: KeyInitializer = DefaultKeyInitializer,
) {

    fun generate(recipe: KeyRecipe): KeyMaterial = when (recipe) {
        KeyRecipe.None -> KeyMaterial.None
        is KeyRecipe.Secret -> KeyMaterial.Secret(secret(recipe))
        is KeyRecipe.Pair -> KeyMaterial.Pairs(List(recipe.count) { pair(recipe) })
        is KeyRecipe.Unavailable -> throw IllegalArgumentException("unavailable_recipe: ${recipe.reason}")
    }

    private fun secret(recipe: KeyRecipe.Secret) =
        KeyGenerator.getInstance(recipe.algorithm, recipe.provider)
            .also { initializer(recipe.provider).initialize(it, recipe.keySize, random) }
            .generateKey()

    private fun pair(recipe: KeyRecipe.Pair) =
        KeyPairGenerator.getInstance(recipe.algorithm, recipe.provider)
            .also { initializer(recipe.provider).initialize(it, recipe.keySize, random) }
            .generateKeyPair()

    private fun initializer(provider: String): KeyInitializer = initializers[provider] ?: fallback
}
