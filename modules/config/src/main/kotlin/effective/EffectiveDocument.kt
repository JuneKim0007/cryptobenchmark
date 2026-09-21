package io.github.junekim0007.cryptobench.config.effective

import io.github.junekim0007.cryptobench.config.effective.dto.EffectiveConfig
import io.github.junekim0007.cryptobench.config.effective.dto.EffectiveEntry
import io.github.junekim0007.cryptobench.config.effective.dto.EffectiveSource
import io.github.junekim0007.cryptobench.config.effective.dto.Skip
import io.github.junekim0007.cryptobench.config.global.PolicyDocument
import io.github.junekim0007.cryptobench.config.inventory.dto.InventorySource
import io.github.junekim0007.cryptobench.config.global.RunDocument
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

    const val GENERATED_FROM = "generatedFrom"
    const val RUN = "run"
    const val POLICY = "policy"
    const val PROVIDERS = "providers"
    const val SKIPPED = "skipped"

    const val KEY_SIZES = "keySizes"
    const val INPUT_SIZES = "inputSizes"
    const val KEY = "key"
    const val PARAMETERS = "parameters"
    const val PROVIDER_DEFAULTS = "providerDefaults"

    private const val GLOBAL = "global"
    private const val TEST_SET = "testSet"
    private const val INVENTORY = "inventory"
    private const val CAPTURE = "capture"
    private const val TRIAL = "trial"
    private const val DEVICE = "device"
    private const val STAGE = "stage"
    private const val PROVIDER = "provider"
    private const val TYPE = "type"
    private const val NAME = "name"
    private const val REASON = "reason"

    override fun of(value: EffectiveConfig): Map<String, Any> = linkedMapOf(
        GENERATED_FROM to value.generatedFrom.let {
            linkedMapOf(GLOBAL to it.global, TEST_SET to it.testSet, INVENTORY to it.inventory,
                CAPTURE to it.environment.capture, TRIAL to it.environment.trial, DEVICE to LinkedHashMap(it.environment.device))
        },
        RUN to RunDocument.of(value.run),
        POLICY to PolicyDocument.of(value.policy),
        PROVIDERS to ProviderTree.of(value.providers) { entry -> entry(entry) },
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
                environment = InventorySource(string(source, CAPTURE), string(source, TRIAL), LinkedHashMap(section(source, DEVICE))),
            ),
            run = RunDocument.parse(section(document, RUN), RUN),
            policy = PolicyDocument.parse(section(document, POLICY), POLICY),
            providers = ProviderTree.parse(section(document, PROVIDERS), PROVIDERS) { entry, _ -> entryOf(entry) },
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
        if (entry.providerDefaults.isNotEmpty()) put(PROVIDER_DEFAULTS, entry.providerDefaults)
    }

    private fun entryOf(document: Map<String, Any>): EffectiveEntry = EffectiveEntry(
        keySizes = optionalNumbers(document, KEY_SIZES),
        inputSizes = optionalNumbers(document, INPUT_SIZES),
        key = optionalSection(document, KEY) ?: emptyMap(),
        parameters = optionalSection(document, PARAMETERS) ?: emptyMap(),
        providerDefaults = optionalStrings(document, PROVIDER_DEFAULTS),
    )
}
