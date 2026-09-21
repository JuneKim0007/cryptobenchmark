package io.github.junekim0007.cryptobench.config.testset

import io.github.junekim0007.cryptobench.config.testset.dto.Override
import io.github.junekim0007.cryptobench.config.testset.dto.TestSet
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.expectKeys
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalNumbersOrNull
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalSection
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalSections
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalString
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.section
import io.github.junekim0007.cryptobench.config.yaml.DocumentHandler

object TestSetDocument : DocumentHandler<TestSet> {

    override val schemaVersion: Int = 1

    private const val DESCRIPTION = "description"
    private const val INCLUDE = "include"
    private const val EXCLUDE = "exclude"
    private const val OVERRIDES = "overrides"
    private const val MATCH = "match"
    private const val SET = "set"
    private const val KEY_SIZES = "keySizes"
    private const val INPUT_SIZES = "inputSizes"
    private const val KEY = "key"
    private const val PARAMETERS = "parameters"

    override fun of(value: TestSet): Map<String, Any> = linkedMapOf(
        DESCRIPTION to value.description,
        INCLUDE to value.include.map { RuleDocument.of(it) },
        EXCLUDE to value.exclude.map { RuleDocument.of(it) },
        OVERRIDES to value.overrides.map { override ->
            linkedMapOf(MATCH to RuleDocument.of(override.match), SET to LinkedHashMap<String, Any>().apply {
                override.keySizes?.let { put(KEY_SIZES, it) }
                override.inputSizes?.let { put(INPUT_SIZES, it) }
                override.key?.let { put(KEY, LinkedHashMap(it)) }
                override.parameters?.let { put(PARAMETERS, LinkedHashMap(it)) }
            })
        },
    )

    override fun parse(document: Map<String, Any>): TestSet {
        expectKeys(document, listOf("schemaVersion", DESCRIPTION, INCLUDE, EXCLUDE, OVERRIDES), "testSet")
        return TestSet(
            description = optionalString(document, DESCRIPTION),
            include = RuleDocument.parseList(optionalSections(document, INCLUDE), INCLUDE),
            exclude = RuleDocument.parseList(optionalSections(document, EXCLUDE), EXCLUDE),
            overrides = optionalSections(document, OVERRIDES).mapIndexed { index, override -> override(override, "$OVERRIDES[$index]") },
        )
    }

    private fun override(document: Map<String, Any>, path: String): Override {
        expectKeys(document, listOf(MATCH, SET), path)
        val set = section(document, SET)
        expectKeys(set, listOf(KEY_SIZES, INPUT_SIZES, KEY, PARAMETERS), "$path.$SET")
        return Override(
            match = RuleDocument.parse(section(document, MATCH), "$path.$MATCH"),
            keySizes = optionalNumbersOrNull(set, KEY_SIZES),
            inputSizes = optionalNumbersOrNull(set, INPUT_SIZES),
            key = optionalSection(set, KEY),
            parameters = optionalSection(set, PARAMETERS),
        )
    }
}
