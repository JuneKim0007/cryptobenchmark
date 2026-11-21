package io.github.junekim0007.cryptobench.config.testset

import io.github.junekim0007.cryptobench.settings.HarnessSettings
import io.github.junekim0007.cryptobench.config.entry.EntryKeys.KEY_SIZES
import io.github.junekim0007.cryptobench.config.entry.EntryKeys.INPUT_SIZES
import io.github.junekim0007.cryptobench.config.entry.EntryKeys.KEY
import io.github.junekim0007.cryptobench.config.entry.EntryKeys.PARAMETERS
import io.github.junekim0007.cryptobench.config.entry.EntryKeys.OPERATIONS
import io.github.junekim0007.cryptobench.config.entry.EntryKeys.HARNESS
import io.github.junekim0007.cryptobench.config.entry.EntryKeys.VARIANTS
import io.github.junekim0007.cryptobench.config.entry.Variants
import io.github.junekim0007.cryptobench.config.testset.dto.Include
import io.github.junekim0007.cryptobench.config.testset.dto.Override
import io.github.junekim0007.cryptobench.config.testset.dto.TestSet
import io.github.junekim0007.cryptobench.document.DocumentFields.expectKeys
import io.github.junekim0007.cryptobench.document.DocumentFields.optional
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalNumbersOrNull
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalSection
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalSections
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalString
import io.github.junekim0007.cryptobench.document.DocumentFields.section
import io.github.junekim0007.cryptobench.document.DocumentFields.strings
import io.github.junekim0007.cryptobench.document.versioned.DocumentHandler
import io.github.junekim0007.cryptobench.document.SchemaVersion

object TestSetDocument : DocumentHandler<TestSet> {

    override val schemaVersion: Int = 1

    private const val DESCRIPTION = "description"
    private const val INCLUDE = "include"
    private const val EXCLUDE = "exclude"
    private const val OVERRIDES = "overrides"
    private const val MATCH = "match"
    private const val SET = "set"

    override fun of(value: TestSet): Map<String, Any> = linkedMapOf(
        DESCRIPTION to value.description,
        INCLUDE to value.include.map { include -> RuleDocument.of(include.rule).let { rule -> include.variants?.let { rule + (VARIANTS to it) } ?: rule } },
        EXCLUDE to value.exclude.map { RuleDocument.of(it) },
        OVERRIDES to value.overrides.map { override ->
            linkedMapOf(MATCH to RuleDocument.of(override.match), SET to LinkedHashMap<String, Any>().apply {
                override.keySizes?.let { put(KEY_SIZES, it) }
                override.inputSizes?.let { put(INPUT_SIZES, it) }
                override.key?.let { put(KEY, LinkedHashMap(it)) }
                override.parameters?.let { put(PARAMETERS, LinkedHashMap(it)) }
                override.operations?.let { put(OPERATIONS, it) }
                override.variants?.let { put(VARIANTS, it) }
                override.harness?.let { put(HARNESS, HarnessSettings.write(it)) }
            })
        },
    )

    override fun parse(document: Map<String, Any>): TestSet {
        expectKeys(document, listOf(SchemaVersion.FIELD, DESCRIPTION, INCLUDE, EXCLUDE, OVERRIDES), "testSet")
        val notices = mutableListOf<String>()
        return TestSet(
            description = optionalString(document, DESCRIPTION),
            include = optionalSections(document, INCLUDE).mapIndexed { index, include -> include(include, "$INCLUDE[$index]", notices) },
            exclude = RuleDocument.parseList(optionalSections(document, EXCLUDE), EXCLUDE),
            overrides = optionalSections(document, OVERRIDES).mapIndexed { index, override -> override(override, "$OVERRIDES[$index]", notices) },
            notices = notices,
        )
    }

    private fun include(document: Map<String, Any>, path: String, notices: MutableList<String>): Include =
        Include(RuleDocument.parse(document, path, listOf(VARIANTS)), variants(document, path, notices))

    private fun variants(document: Map<String, Any>, path: String, notices: MutableList<String>): List<String>? =
        Variants.read(document, VARIANTS, "$path.$VARIANTS")?.also { read -> read.notice?.let { notices += it } }?.values

    private fun override(document: Map<String, Any>, path: String, notices: MutableList<String>): Override {
        expectKeys(document, listOf(MATCH, SET), path)
        val set = section(document, SET)
        expectKeys(set, listOf(KEY_SIZES, INPUT_SIZES, KEY, PARAMETERS, OPERATIONS, VARIANTS, HARNESS), "$path.$SET")
        return Override(
            match = RuleDocument.parse(section(document, MATCH), "$path.$MATCH"),
            keySizes = optionalNumbersOrNull(set, KEY_SIZES),
            inputSizes = optionalNumbersOrNull(set, INPUT_SIZES),
            key = optionalSection(set, KEY),
            parameters = optionalSection(set, PARAMETERS),
            operations = optional(set, OPERATIONS, null, ::strings),
            variants = variants(set, "$path.$SET", notices),
            harness = optionalSection(set, HARNESS)?.let { HarnessSettings.read(it, "$path.$SET.$HARNESS") },
        )
    }
}
