package io.github.junekim0007.cryptobench.preparation.key.plan

/** Where a case's key comes from: algorithm null is the measured key; provider `same` is the case's own, any other name only when written. */
data class KeySource(val algorithm: String? = null, val provider: String = SAME) {

    val written: Boolean get() = algorithm != null || provider != SAME

    fun providerFor(caseProvider: String): String = if (provider == SAME) caseProvider else provider

    fun asMap(): Map<String, Any> = listOfNotNull(algorithm?.let { ALGORITHM to it }, (PROVIDER to provider).takeIf { written }).toMap()

    companion object {
        const val ALGORITHM = "algorithm"
        const val PROVIDER = "provider"
        const val SAME = "same"

        /** An entry's key block split into its source and the spec tree the generator binds. */
        fun split(key: Map<String, Any>, path: String): Pair<KeySource, Map<String, Any>> {
            val named = listOf(ALGORITHM, PROVIDER).associateWith { key[it] }.filterValues { it != null }
            require(named.values.all { it is String && it.isNotBlank() }) { "invalid: $path $named, a name each" }
            return KeySource(named[ALGORITHM] as String?, named[PROVIDER] as String? ?: SAME) to key.filterKeys { it !in named }
        }
    }
}
