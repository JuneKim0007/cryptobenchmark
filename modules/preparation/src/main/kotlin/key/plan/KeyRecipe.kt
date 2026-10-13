package io.github.junekim0007.cryptobench.preparation.key.plan

sealed class KeyRecipe {

    abstract val kind: String


    object None : KeyRecipe() {
        override val kind: String = "none"
    }

    data class Secret(
        val algorithm: String,
        val keySize: Int?,
        val provider: String,
        val parameters: Map<String, Any> = emptyMap(),
    ) : KeyRecipe() {
        override val kind: String = "secret"
    }

    data class Pair(
        val algorithm: String,
        val keySize: Int?,
        val provider: String,
        val count: Int = 1,
        val parameters: Map<String, Any> = emptyMap(),
    ) : KeyRecipe() {
        override val kind: String = "pair"

        init {
            require(count >= 1) { "not_positive: count $count" }
        }
    }

    data class Unavailable(val reason: String) : KeyRecipe() {
        override val kind: String = "unavailable"
    }
}
