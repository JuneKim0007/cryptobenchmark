package io.github.junekim0007.cryptobench.config.effective

import io.github.junekim0007.cryptobench.config.entry.EntryKeys.KEY_SIZES
import io.github.junekim0007.cryptobench.config.entry.EntryKeys.INPUT_SIZES
import io.github.junekim0007.cryptobench.config.entry.EntryKeys.KEY
import io.github.junekim0007.cryptobench.config.entry.EntryKeys.PARAMETERS
import io.github.junekim0007.cryptobench.config.entry.EntryKeys.OPERATIONS
import io.github.junekim0007.cryptobench.config.entry.EntryKeys.HARNESS
import io.github.junekim0007.cryptobench.config.effective.dto.EffectiveConfig
import io.github.junekim0007.cryptobench.config.effective.dto.EffectiveEntry
import io.github.junekim0007.cryptobench.config.effective.dto.EffectiveSource
import io.github.junekim0007.cryptobench.config.global.AnalysisDocument
import io.github.junekim0007.cryptobench.config.global.PolicyDocument
import io.github.junekim0007.cryptobench.config.inventory.InventorySourceDocument
import io.github.junekim0007.cryptobench.config.harness.HarnessDocument
import io.github.junekim0007.cryptobench.config.global.RunDocument
import io.github.junekim0007.cryptobench.config.global.dto.AnalysisSettings
import io.github.junekim0007.cryptobench.config.harness.HarnessSettings
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalNumbers
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalSection
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalSections
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
    private const val RUN_ID = "runId"
    private const val PROVIDERS = "providers"
    private const val SKIPPED = "skipped"
    private const val WARNINGS = "warnings"

    private const val PROVIDER_DEFAULTS = "providerDefaults"

    private const val GLOBAL = "global"
    private const val TEST_SET = "testSet"
    private const val INVENTORY = "inventory"

    override fun of(value: EffectiveConfig): Map<String, Any> = LinkedHashMap<String, Any>().apply {
        put(GENERATED_FROM, LinkedHashMap<String, Any>().apply {
            put(GLOBAL, value.generatedFrom.global)
            put(TEST_SET, value.generatedFrom.testSet)
            put(INVENTORY, value.generatedFrom.inventory)
            putAll(InventorySourceDocument.of(value.generatedFrom.environment))
        })
        value.runId?.let { put(RUN_ID, it) }
        put(RUN, RunDocument.of(value.run))
        put(POLICY, PolicyDocument.of(value.policy))
        put(ANALYSIS, AnalysisDocument.of(value.analysis))
        put(PROVIDERS, ProviderTree.of(value.providers, ::entry))
    }

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
            skipped = optionalSections(document, SKIPPED).map { SkipDocument.parse(it) },
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
