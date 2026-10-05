package io.github.junekim0007.cryptobench.config.effective

import io.github.junekim0007.cryptobench.config.effective.dto.EffectiveConfig
import io.github.junekim0007.cryptobench.config.effective.dto.EffectiveEntry
import io.github.junekim0007.cryptobench.config.effective.dto.EffectiveSource
import io.github.junekim0007.cryptobench.config.effective.dto.Skip
import io.github.junekim0007.cryptobench.config.global.AnalysisDocument
import io.github.junekim0007.cryptobench.config.global.PolicyDocument
import io.github.junekim0007.cryptobench.config.inventory.InventorySourceDocument
import io.github.junekim0007.cryptobench.config.global.HarnessDocument
import io.github.junekim0007.cryptobench.config.global.RunDocument
import io.github.junekim0007.cryptobench.config.global.dto.AnalysisSettings
import io.github.junekim0007.cryptobench.config.global.dto.HarnessSettings
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalNumbers
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalSection
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalSections
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalStringOrNull
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalStrings
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.section
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.string
import io.github.junekim0007.cryptobench.config.yaml.DocumentHandler
import io.github.junekim0007.cryptobench.config.yaml.ProviderTree

object EffectiveDocument : DocumentHandler<EffectiveConfig> {

    override val schemaVersion: Int = 1

    private const val GENERATED_FROM = "generatedFrom"
    private const val RUN = "run"
    private const val POLICY = "policy"
    private const val ANALYSIS = "analysis"
    private const val PROVIDERS = "providers"
    private const val SKIPPED = "skipped"
    private const val WARNINGS = "warnings"

    private const val KEY_SIZES = "keySizes"
    private const val INPUT_SIZES = "inputSizes"
    private const val KEY = "key"
    private const val PARAMETERS = "parameters"
    private const val PROVIDER_DEFAULTS = "providerDefaults"
    private const val OPERATIONS = "operations"
    private const val HARNESS = "harness"

    private const val GLOBAL = "global"
    private const val TEST_SET = "testSet"
    private const val INVENTORY = "inventory"
    private const val STAGE = "stage"
    private const val PROVIDER = "provider"
    private const val TYPE = "type"
    private const val NAME = "name"
    private const val REASON = "reason"

    override fun of(value: EffectiveConfig): Map<String, Any> = linkedMapOf(
        GENERATED_FROM to LinkedHashMap<String, Any>().apply {
            put(GLOBAL, value.generatedFrom.global)
            put(TEST_SET, value.generatedFrom.testSet)
            put(INVENTORY, value.generatedFrom.inventory)
            putAll(InventorySourceDocument.of(value.generatedFrom.environment))
        },
        RUN to RunDocument.of(value.run),
        POLICY to PolicyDocument.of(value.policy),
        ANALYSIS to AnalysisDocument.of(value.analysis),
        PROVIDERS to ProviderTree.of(value.providers, ::entry),
        WARNINGS to value.warnings,
        SKIPPED to value.skipped.map { skip ->
            LinkedHashMap<String, Any>().apply {
                put(STAGE, skip.stage)
                skip.provider?.let { put(PROVIDER, it) }
                skip.type?.let { put(TYPE, it) }
                skip.name?.let { put(NAME, it) }
                put(REASON, skip.reason)
            }
        },
    )

    override fun parse(document: Map<String, Any>): EffectiveConfig {
        val source = section(document, GENERATED_FROM)
        return EffectiveConfig(
            generatedFrom = EffectiveSource(
                global = string(source, GLOBAL),
                testSet = string(source, TEST_SET),
                inventory = string(source, INVENTORY),
                environment = InventorySourceDocument.parse(source),
            ),
            run = RunDocument.parse(section(document, RUN), RUN),
            policy = PolicyDocument.parse(section(document, POLICY), POLICY),
            analysis = optionalSection(document, ANALYSIS)?.let { AnalysisDocument.parse(it, ANALYSIS) } ?: AnalysisSettings(),
            providers = ProviderTree.parse(section(document, PROVIDERS), PROVIDERS, ::entryOf),
            warnings = optionalStrings(document, WARNINGS),
            skipped = optionalSections(document, SKIPPED).map { skip ->
                Skip(string(skip, STAGE), optionalStringOrNull(skip, PROVIDER), optionalStringOrNull(skip, TYPE), optionalStringOrNull(skip, NAME), string(skip, REASON))
            },
        )
    }

    private fun entry(entry: EffectiveEntry): Map<String, Any> = LinkedHashMap<String, Any>().apply {
        if (entry.keySizes.isNotEmpty()) put(KEY_SIZES, entry.keySizes)
        if (entry.inputSizes.isNotEmpty()) put(INPUT_SIZES, entry.inputSizes)
        if (entry.key.isNotEmpty()) put(KEY, LinkedHashMap(entry.key))
        if (entry.parameters.isNotEmpty()) put(PARAMETERS, LinkedHashMap(entry.parameters))
        if (entry.operations.isNotEmpty()) put(OPERATIONS, entry.operations)
        if (entry.providerDefaults.isNotEmpty()) put(PROVIDER_DEFAULTS, entry.providerDefaults)
        if (!entry.harness.isEmpty) put(HARNESS, HarnessDocument.of(entry.harness))
    }

    private fun entryOf(document: Map<String, Any>): EffectiveEntry = EffectiveEntry(
        keySizes = optionalNumbers(document, KEY_SIZES),
        inputSizes = optionalNumbers(document, INPUT_SIZES),
        key = optionalSection(document, KEY) ?: emptyMap(),
        parameters = optionalSection(document, PARAMETERS) ?: emptyMap(),
        providerDefaults = optionalStrings(document, PROVIDER_DEFAULTS),
        operations = optionalStrings(document, OPERATIONS),
        harness = optionalSection(document, HARNESS)?.let { HarnessDocument.parse(it, HARNESS) } ?: HarnessSettings(),
    )
}
