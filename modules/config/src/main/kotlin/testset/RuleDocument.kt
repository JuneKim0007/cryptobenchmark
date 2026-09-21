package io.github.junekim0007.cryptobench.config.testset

import io.github.junekim0007.cryptobench.config.testset.dto.Rule
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.asSection
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.expectKeys
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalStringOrNull

object RuleDocument {

    private const val PROVIDER = "provider"
    private const val TYPE = "type"
    private const val NAME = "name"

    fun of(rule: Rule): Map<String, Any> = LinkedHashMap<String, Any>().apply {
        rule.provider?.let { put(PROVIDER, it) }
        rule.type?.let { put(TYPE, it) }
        rule.name?.let { put(NAME, it) }
    }

    fun parse(value: Any, path: String): Rule {
        val document = asSection(value, path)
        expectKeys(document, listOf(PROVIDER, TYPE, NAME), path)
        return try {
            Rule(optionalStringOrNull(document, PROVIDER), optionalStringOrNull(document, TYPE), optionalStringOrNull(document, NAME))
        } catch (failure: IllegalArgumentException) {
            throw IllegalArgumentException("${failure.message} at $path", failure)
        }
    }

    fun parseList(values: List<Map<String, Any>>, path: String): List<Rule> =
        values.mapIndexed { index, value -> parse(value, "$path[$index]") }
}
