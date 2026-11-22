package io.github.junekim0007.cryptobench.contract.bundled

data class BundledProvider(
    val artifact: String,
    val create: String,
    val alias: String? = null,
) {

    val className: String get() = create.substringBefore(FACTORY)

    val factory: String? get() = create.substringAfter(FACTORY, "").ifEmpty { null }

    init {
        require(ARTIFACT.matches(artifact)) { "invalid_artifact: $artifact, expected group:name:version" }
        require(CREATE.matches(create)) { "invalid_create: $create, expected fully.qualified.Class or fully.qualified.Class#staticFactory" }
        require(alias == null || NAME.matches(alias)) { "invalid_alias: '$alias', expected a non-blank name without whitespace" }
    }

    private companion object {
        const val FACTORY = '#'
        // Java's \s spelled out: ART's ICU regex gives \s another set
        private const val SPACE = " \\t\\n\\u000B\\f\\r"
        private const val PART = "[^:,$SPACE]+"
        val ARTIFACT = Regex("$PART:$PART:$PART")
        private const val IDENTIFIER = "[\\p{L}_$][\\p{L}\\p{N}_$]*"
        val CREATE = Regex("$IDENTIFIER(\\.$IDENTIFIER)+(#$IDENTIFIER)?")
        val NAME = Regex("[^$SPACE]+")
    }
}
