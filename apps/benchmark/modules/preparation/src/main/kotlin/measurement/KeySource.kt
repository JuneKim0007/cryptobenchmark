package io.github.junekim0007.cryptobench.preparation.measurement

/** Where a case's key comes from: algorithm null is the measured key; provider `same` the case's own, `any` the case's own then every provider, else the named one. */
data class KeySource(val algorithm: String? = null, val provider: String = SAME) {

    val written: Boolean get() = algorithm != null || provider != SAME

    /** The providers whose generator may make the key, in the order they are tried. */
    fun providers(caseProvider: String, installed: List<String>): List<String> = when (provider) {
        SAME -> listOf(caseProvider)
        ANY -> (listOf(caseProvider) + installed).distinct()
        else -> listOf(provider)
    }

    fun label(caseProvider: String): String = when (provider) {
        SAME -> caseProvider
        ANY -> "any provider"
        else -> provider
    }

    // `any` alone leaves the case id as it was: on one device it is the default key or no case at all
    fun identity(): Map<String, Any> = listOfNotNull(algorithm?.let { ALGORITHM to it }, (PROVIDER to provider).takeIf { it.second !in setOf(SAME, ANY) }).toMap()

    companion object {
        const val ALGORITHM = "algorithm"
        const val PROVIDER = "provider"
        const val SAME = "same"
        const val ANY = "any"

        /** An entry's key block split into its source and the spec tree the generator binds. */
        fun split(key: Map<String, Any>, path: String): Pair<KeySource, Map<String, Any>> {
            val named = listOf(ALGORITHM, PROVIDER).associateWith { key[it] }.filterValues { it != null }
            require(named.values.all { it is String && it.isNotBlank() }) { "invalid: $path $named, a name each" }
            return KeySource(named[ALGORITHM] as String?, named[PROVIDER] as String? ?: SAME) to key.filterKeys { it !in named }
        }
    }
}
