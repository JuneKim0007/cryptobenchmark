package io.github.junekim0007.cryptobench.benchmark.preparation.key.plan

/** How to make the key one case needs; `provider` is who generates it, which may differ from who uses it. */
sealed class KeyRecipe {

    object None : KeyRecipe()

    data class Secret(val algorithm: String, val keySize: Int?, val provider: String) : KeyRecipe()

    data class Pair(val algorithm: String, val keySize: Int?, val provider: String, val count: Int = 1) : KeyRecipe() {
        init {
            require(count >= 1) { "not_positive: count $count" }
        }
    }

    data class Unavailable(val reason: String) : KeyRecipe()
}
