package io.github.junekim0007.cryptobench.preparation.key.generate

import io.github.junekim0007.cryptobench.preparation.key.plan.KeyRecipe
import io.github.junekim0007.cryptobench.jca.bind.ParameterBinder
import io.github.junekim0007.cryptobench.jca.peer.PeerPair
import java.security.KeyPair
import java.security.KeyPairGenerator
import java.security.SecureRandom
import java.security.spec.AlgorithmParameterSpec
import javax.crypto.KeyGenerator

class KeyMaterialGenerator(private val binder: ParameterBinder = ParameterBinder()) {

    private val random = SecureRandom()

    fun generate(recipe: KeyRecipe): KeyMaterial = when (recipe) {
        KeyRecipe.None -> KeyMaterial.None
        is KeyRecipe.Secret -> KeyMaterial.Secret(secret(recipe))
        is KeyRecipe.Pair -> KeyMaterial.Pairs(pair(recipe).let { own -> listOf(own) + List(recipe.count - 1) { peer(own, recipe) } })
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

    // a second pair is the first one's peer: same curve or group, so the two agree
    private fun peer(own: KeyPair, recipe: KeyRecipe.Pair) = PeerPair.of(own, KeyPairGenerator.getInstance(recipe.algorithm, recipe.provider), random)

    private fun spec(parameters: Map<String, Any>): AlgorithmParameterSpec? =
        if (parameters.isEmpty()) null else binder.bind(parameters, "key").next()
}
