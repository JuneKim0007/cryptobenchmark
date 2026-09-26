package io.github.junekim0007.cryptobench.config.testset

import io.github.junekim0007.cryptobench.config.testset.dto.Rule
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.asSection
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.expectKeys
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalStringOrNull
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.withPathInFailure

object RuleDocument {

    private const val PROVIDER = "provider"
    private const val TYPE = "type"
    private const val NAME = "name"
    private const val GROUP = "group"

    fun of(rule: Rule): Map<String, Any> = LinkedHashMap<String, Any>().apply {
        rule.provider?.let { put(PROVIDER, it) }
        rule.type?.let { put(TYPE, it) }
        rule.name?.let { put(NAME, it) }
        rule.group?.let { put(GROUP, it) }
    }

    fun parse(value: Any, path: String): Rule {
        val document = asSection(value, path)
        expectKeys(document, listOf(PROVIDER, TYPE, NAME, GROUP), path)
        return withPathInFailure(path) {
            Rule(optionalStringOrNull(document, PROVIDER), optionalStringOrNull(document, TYPE), optionalStringOrNull(document, NAME), optionalStringOrNull(document, GROUP))
        }
    }

    fun parseList(values: List<Map<String, Any>>, path: String): List<Rule> =
        values.mapIndexed { index, value -> parse(value, "$path[$index]") }
}
