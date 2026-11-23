package io.github.junekim0007.cryptobench.config.effective

import io.github.junekim0007.cryptobench.config.entry.EntryKeys.KEY_SIZES
import io.github.junekim0007.cryptobench.config.entry.EntryKeys.INPUT_SIZES
import io.github.junekim0007.cryptobench.config.entry.EntryKeys.KEY
import io.github.junekim0007.cryptobench.config.entry.EntryKeys.PARAMETERS
import io.github.junekim0007.cryptobench.config.entry.EntryKeys.OPERATIONS
import io.github.junekim0007.cryptobench.config.entry.EntryKeys.HARNESS
import io.github.junekim0007.cryptobench.config.entry.EntryKeys.VARIANTS
import io.github.junekim0007.cryptobench.config.effective.dto.EffectiveConfig
import io.github.junekim0007.cryptobench.config.effective.dto.EffectiveEntry
import io.github.junekim0007.cryptobench.config.effective.dto.EffectiveSource
import io.github.junekim0007.cryptobench.config.effective.dto.EntryOrigin
import io.github.junekim0007.cryptobench.config.testset.RuleDocument
import io.github.junekim0007.cryptobench.config.global.AnalysisDocument
import io.github.junekim0007.cryptobench.config.global.PolicyDocument
import io.github.junekim0007.cryptobench.contract.bundled.BundledProvider
import io.github.junekim0007.cryptobench.config.inventory.InventorySourceDocument
import io.github.junekim0007.cryptobench.settings.HarnessSettings
import io.github.junekim0007.cryptobench.config.global.RunDocument
import io.github.junekim0007.cryptobench.config.global.dto.AnalysisSettings
import io.github.junekim0007.cryptobench.document.DocumentFields.number
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalNumbers
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalSection
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalSections
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalStrings
import io.github.junekim0007.cryptobench.document.DocumentFields.section
import io.github.junekim0007.cryptobench.document.DocumentFields.sections
import io.github.junekim0007.cryptobench.config.layers.LayerStack
import io.github.junekim0007.cryptobench.document.DocumentFields.string
import io.github.junekim0007.cryptobench.document.versioned.DocumentHandler
import io.github.junekim0007.cryptobench.config.yaml.ProviderTree
import io.github.junekim0007.cryptobench.records.Skip

object EffectiveDocument : DocumentHandler<EffectiveConfig> {

    override val schemaVersion: Int = 2

    private const val GENERATED_FROM = "generatedFrom"
    private const val RUN = "run"
    private const val POLICY = "policy"
    private const val ANALYSIS = "analysis"
    private const val RUN_ID = "runId"
    private const val PROVIDERS = "providers"
    private const val SKIPPED = "skipped"
    private const val WARNINGS = "warnings"
    private const val BUNDLED_PROVIDERS = "bundledProviders"

    private const val PROVIDER_DEFAULTS = "providerDefaults"
    private const val FROM = "from"
    private const val INCLUDES = "includes"
    private const val INDEX = "index"

    private const val LAYERS = "layers"
    private const val SETTINGS = "settings"
    private const val PATH = "path"
    private const val SHA256 = "sha256"

    private const val GLOBAL = "global"
    private const val TEST_SET = "testSet"
    private const val INVENTORY = "inventory"

    override fun of(value: EffectiveConfig): Map<String, Any> = LinkedHashMap<String, Any>().apply {
        put(GENERATED_FROM, LinkedHashMap<String, Any>().apply {
            put(GLOBAL, value.generatedFrom.global)
            put(TEST_SET, value.generatedFrom.testSet)
            put(INVENTORY, value.generatedFrom.inventory)
            putAll(InventorySourceDocument.of(value.generatedFrom.environment))
            put(LAYERS, value.generatedFrom.layers.map { linkedMapOf(PATH to it.path, SHA256 to it.sha256) })
            put(SETTINGS, LinkedHashMap(value.generatedFrom.settings))
        })
        value.runId?.let { put(RUN_ID, it) }
        put(RUN, RunDocument.of(value.run))
        put(POLICY, PolicyDocument.of(value.policy))
        put(ANALYSIS, AnalysisDocument.of(value.analysis))
        if (value.bundledProviders.isNotEmpty()) put(BUNDLED_PROVIDERS, value.bundledProviders.map(BundledProvider::entry))
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
                layers = sections(source, LAYERS).map { LayerStack.Layer(string(it, PATH), string(it, SHA256)) },
                settings = section(source, SETTINGS).mapValues { (key, value) -> value as? String ?: throw IllegalArgumentException("wrong_type: $GENERATED_FROM.$SETTINGS.$key") },
            ),
            run = RunDocument.parse(section(document, RUN), RUN),
            policy = PolicyDocument.parse(section(document, POLICY), POLICY),
            analysis = optionalSection(document, ANALYSIS)?.let { AnalysisDocument.parse(it, ANALYSIS) } ?: AnalysisSettings(),
            providers = ProviderTree.parse(section(document, PROVIDERS), PROVIDERS, ::entryOf),
            warnings = optionalStrings(document, WARNINGS),
            skipped = optionalSections(document, SKIPPED).map(Skip::read),
            bundledProviders = BundledProvider.parseList(optionalSections(document, BUNDLED_PROVIDERS), BUNDLED_PROVIDERS),
        )
    }

    /** The run, policy and analysis sections as of() writes them: what generatedFrom.settings names a source for. */
    fun settingsOf(value: EffectiveConfig): Map<String, Any> =
        linkedMapOf(RUN to RunDocument.of(value.run), POLICY to PolicyDocument.of(value.policy), ANALYSIS to AnalysisDocument.of(value.analysis))

    private fun entry(entry: EffectiveEntry): Map<String, Any> = LinkedHashMap<String, Any>().apply {
        if (entry.keySizes.isNotEmpty()) put(KEY_SIZES, entry.keySizes)
        if (entry.inputSizes.isNotEmpty()) put(INPUT_SIZES, entry.inputSizes)
        if (entry.key.isNotEmpty()) put(KEY, LinkedHashMap(entry.key))
        if (entry.parameters.isNotEmpty()) put(PARAMETERS, LinkedHashMap(entry.parameters))
        if (entry.operations.isNotEmpty()) put(OPERATIONS, entry.operations)
        if (entry.variants.isNotEmpty()) put(VARIANTS, entry.variants)
        if (entry.providerDefaults.isNotEmpty()) put(PROVIDER_DEFAULTS, entry.providerDefaults)
        if (!entry.harness.isEmpty) put(HARNESS, HarnessSettings.write(entry.harness))
        entry.from?.let { from -> put(FROM, LinkedHashMap<String, Any>().apply {
            put(TEST_SET, from.testSet)
            if (from.includes.isNotEmpty()) put(INCLUDES, from.includes.map { (index, rule) -> linkedMapOf<String, Any>(INDEX to index) + RuleDocument.of(rule) })
        }) }
    }

    private fun originOf(document: Map<String, Any>): EntryOrigin = EntryOrigin(
        testSet = string(document, TEST_SET),
        includes = optionalSections(document, INCLUDES).withIndex().associate { (at, include) ->
            number(include, INDEX).toInt() to RuleDocument.parse(include, "$FROM.$INCLUDES[$at]", listOf(INDEX))
        },
    )

    private fun entryOf(document: Map<String, Any>): EffectiveEntry = EffectiveEntry(
        keySizes = optionalNumbers(document, KEY_SIZES),
        inputSizes = optionalNumbers(document, INPUT_SIZES),
        key = optionalSection(document, KEY) ?: emptyMap(),
        parameters = optionalSection(document, PARAMETERS) ?: emptyMap(),
        providerDefaults = optionalStrings(document, PROVIDER_DEFAULTS),
        operations = optionalStrings(document, OPERATIONS),
        variants = optionalStrings(document, VARIANTS),
        harness = optionalSection(document, HARNESS)?.let { HarnessSettings.read(it, HARNESS) } ?: HarnessSettings(),
        from = optionalSection(document, FROM)?.let(::originOf),
    )
}
