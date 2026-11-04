package io.github.junekim0007.cryptobench.config.global.dto

data class BundledProvider(
    val artifact: String,
    val create: String,
    val alias: String? = null,
) {

    init {
        require(ARTIFACT.matches(artifact)) { "invalid_artifact: $artifact, expected group:name:version" }
        require(CREATE.matches(create)) { "invalid_create: $create, expected fully.qualified.Class or fully.qualified.Class#staticFactory" }
        require(alias == null || NAME.matches(alias)) { "invalid_alias: '$alias', expected a non-blank name without whitespace" }
    }

    private companion object {
        val ARTIFACT = Regex("[^:,\\s]+:[^:,\\s]+:[^:,\\s]+")
        private const val IDENTIFIER = "[\\p{L}_$][\\p{L}\\p{N}_$]*"
        val CREATE = Regex("$IDENTIFIER(\\.$IDENTIFIER)+(#$IDENTIFIER)?")
        val NAME = Regex("\\S+")
    }
}
