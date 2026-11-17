package io.github.junekim0007.cryptobench.preparation.measurement

/**
 * Where a case's key comes from: algorithm null is the measured key; provider `same` the case's own, `any` the case's own then every provider,
 * else the named one; backing null is tee, where a secure key is born unless strongbox is written.
 */
data class KeySource(val algorithm: String? = null, val provider: String = SAME, val backing: String? = null) {

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

    val requestedBacking: String get() = backing ?: TEE

    // `any` alone and the default backing leave the case id as it was: on one device it is the default key or no case at all
    fun identity(): Map<String, Any> = listOfNotNull(algorithm?.let { ALGORITHM to it }, (PROVIDER to provider).takeIf { it.second !in setOf(SAME, ANY) },
        backing?.takeIf { it != TEE }?.let { BACKING to it }).toMap()

    companion object {
        const val ALGORITHM = "algorithm"
        const val PROVIDER = "provider"
        const val SAME = "same"
        const val ANY = "any"
        const val BACKING = "backing"
        const val TEE = "tee"
        val BACKINGS = listOf(TEE, "strongbox")

        /** An entry's key block split into its source and the spec tree the generator binds. */
        fun split(key: Map<String, Any>, path: String): Pair<KeySource, Map<String, Any>> {
            val named = listOf(ALGORITHM, PROVIDER, BACKING).associateWith { key[it] }.filterValues { it != null }
            require(named.values.all { it is String && it.isNotBlank() }) { "invalid: $path $named, a name each" }
            require(named[BACKING]?.let { it in BACKINGS } ?: true) { "invalid: $path.$BACKING ${named[BACKING]}, one of $BACKINGS" }
            return KeySource(named[ALGORITHM] as String?, named[PROVIDER] as String? ?: SAME, named[BACKING] as String?) to key.filterKeys { it !in named }
        }
    }
}
