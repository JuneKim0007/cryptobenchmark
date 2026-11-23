package io.github.junekim0007.cryptobench.contract.bundled

import io.github.junekim0007.cryptobench.document.DocumentFields.expectKeys
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalStringOrNull
import io.github.junekim0007.cryptobench.document.DocumentFields.string
import io.github.junekim0007.cryptobench.document.DocumentFields.withPathInFailure

data class BundledProvider(
    val artifact: String,
    val create: String,
    val alias: String? = null,
) {

    val className: String get() = create.substringBefore(FACTORY)

    val factory: String? get() = create.substringAfter(FACTORY, "").ifEmpty { null }

    init {
        require(ARTIFACT_FORM.matches(artifact)) { "invalid_artifact: $artifact, expected group:name:version" }
        require(CREATE_FORM.matches(create)) { "invalid_create: $create, expected fully.qualified.Class or fully.qualified.Class#staticFactory" }
        require(alias == null || NAME_FORM.matches(alias)) { "invalid_alias: '$alias', expected a non-blank name without whitespace" }
    }

    fun entry(): Map<String, Any> = linkedMapOf<String, Any>(ARTIFACT to artifact, CREATE to create).apply { alias?.let { put(ALIAS, it) } }

    companion object {
        const val KEY = "bundledProviders"
        private const val ARTIFACT = "artifact"
        private const val CREATE = "create"
        private const val ALIAS = "alias"
        private const val FACTORY = '#'
        // Java's \s spelled out: ART's ICU regex gives \s another set
        private const val SPACE = " \\t\\n\\u000B\\f\\r"
        private const val PART = "[^:,$SPACE]+"
        private val ARTIFACT_FORM = Regex("$PART:$PART:$PART")
        private const val IDENTIFIER = "[\\p{L}_$][\\p{L}\\p{N}_$]*"
        private val CREATE_FORM = Regex("$IDENTIFIER(\\.$IDENTIFIER)+(#$IDENTIFIER)?")
        private val NAME_FORM = Regex("[^$SPACE]+")

        fun parse(entry: Map<String, Any>, at: String): BundledProvider {
            expectKeys(entry, listOf(ARTIFACT, CREATE, ALIAS), at)
            return withPathInFailure(at) { BundledProvider(string(entry, ARTIFACT), string(entry, CREATE), optionalStringOrNull(entry, ALIAS)) }
        }

        // every entry first, then repeated artifacts, then repeated aliases
        fun parseList(entries: List<Map<String, Any>>, path: String): List<BundledProvider> {
            val parsed = entries.mapIndexed { index, entry -> parse(entry, "$path[$index]") }
            withPathInFailure(path) {
                repeated(parsed.map { it.artifact }).let { require(it.isEmpty()) { "duplicate_artifact: $it" } }
                repeated(parsed.mapNotNull { it.alias }).let { require(it.isEmpty()) { "duplicate_alias: $it" } }
            }
            return parsed
        }

        private fun repeated(values: List<String>): List<String> = values.groupBy { it }.filterValues { it.size > 1 }.keys.toList()
    }
}
