package io.github.junekim0007.cryptobench.discovery.bundled

data class BundledProvider(
    val artifact: String,
    val create: String,
    val alias: String? = null,
) {

    val className: String get() = create.substringBefore(FACTORY)

    val factory: String? get() = create.substringAfter(FACTORY, "").ifEmpty { null }

    init {
        if (artifact.isBlank()) throw BundledProviderException("blank_artifact", create)
        if (!CREATE.matches(create)) throw BundledProviderException("invalid_create", "$create, expected Class or Class#staticFactory")
        if (alias != null && alias.isBlank()) throw BundledProviderException("blank_alias", artifact)
    }

    private companion object {
        const val FACTORY = '#'
        private const val IDENTIFIER = "[\\p{L}_$][\\p{L}\\p{N}_$]*"
        val CREATE = Regex("$IDENTIFIER(\\.$IDENTIFIER)+(#$IDENTIFIER)?")
    }
}
