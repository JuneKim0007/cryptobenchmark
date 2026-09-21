package io.github.junekim0007.cryptobench.preparation.key.plan

sealed class KeyRecipe {

    object None : KeyRecipe()

    data class Secret(
        val algorithm: String,
        val keySize: Int?,
        val provider: String,
        val parameters: Map<String, Any> = emptyMap(),
    ) : KeyRecipe()

    data class Pair(
        val algorithm: String,
        val keySize: Int?,
        val provider: String,
        val count: Int = 1,
        val parameters: Map<String, Any> = emptyMap(),
    ) : KeyRecipe() {
        init {
            require(count >= 1) { "not_positive: count $count" }
        }
    }

    data class Unavailable(val reason: String) : KeyRecipe()
}
