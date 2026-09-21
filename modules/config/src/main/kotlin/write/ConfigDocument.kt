package io.github.junekim0007.cryptobench.config.write

import io.github.junekim0007.cryptobench.config.contract.BenchmarkConfig
import io.github.junekim0007.cryptobench.config.contract.ConfigEntry
import io.github.junekim0007.cryptobench.config.contract.GeneratedFrom
import io.github.junekim0007.cryptobench.config.contract.RunSettings
import io.github.junekim0007.cryptobench.config.write.DocumentFields.asSection
import io.github.junekim0007.cryptobench.config.write.DocumentFields.boolean
import io.github.junekim0007.cryptobench.config.write.DocumentFields.number
import io.github.junekim0007.cryptobench.config.write.DocumentFields.numbers
import io.github.junekim0007.cryptobench.config.write.DocumentFields.optionalBoolean
import io.github.junekim0007.cryptobench.config.write.DocumentFields.optionalNumbers
import io.github.junekim0007.cryptobench.config.write.DocumentFields.optionalSection
import io.github.junekim0007.cryptobench.config.write.DocumentFields.optionalString
import io.github.junekim0007.cryptobench.config.write.DocumentFields.section
import io.github.junekim0007.cryptobench.config.write.DocumentFields.string
import io.github.junekim0007.cryptobench.config.write.DocumentFields.strings

/** The default.yaml schema. Encodes and decodes in one place, so a renamed key fails a round trip. */
object ConfigDocument {

    const val SCHEMA_VERSION = "schemaVersion"
    const val GENERATED_FROM = "generatedFrom"
    const val RUN = "run"
    const val PROVIDERS = "providers"

    const val CAPTURE = "capture"
    const val TRIAL = "trial"
    const val DEVICE = "device"

    const val INPUT_SIZES = "inputSizes"
    const val PHASES = "phases"
    const val METRICS = "metrics"
    const val PROCESS_REPETITIONS = "processRepetitions"
    const val SEED = "seed"

    const val ENABLED = "enabled"
    const val KEY_SIZES = "keySizes"
    const val KEY_ALGORITHM = "keyAlgorithm"
    const val KEY_PROVIDER = "keyProvider"
    const val PROVIDER_CHOSE = "providerChose"
    const val BARE_NAME = "bareName"
    const val REASON = "reason"
    const val KEY = "key"
    const val PARAMETERS = "parameters"

    fun of(config: BenchmarkConfig): Map<String, Any> = linkedMapOf(
        SCHEMA_VERSION to config.schemaVersion,
        GENERATED_FROM to linkedMapOf(
            CAPTURE to config.generatedFrom.capture,
            TRIAL to config.generatedFrom.trial,
            DEVICE to LinkedHashMap(config.generatedFrom.device),
        ),
        RUN to runDocument(config.run),
        PROVIDERS to config.providers.mapValuesTo(LinkedHashMap()) { (_, types) ->
            types.mapValuesTo(LinkedHashMap()) { (_, entries) ->
                entries.mapValuesTo(LinkedHashMap()) { (_, entry) -> entryDocument(entry) }
            }
        },
    )

    fun parse(document: Map<String, Any>): BenchmarkConfig {
        val schemaVersion = number(document, SCHEMA_VERSION).toInt()
        require(schemaVersion == BenchmarkConfig.SCHEMA_VERSION) {
            "unsupported_schema_version: $schemaVersion, this build reads ${BenchmarkConfig.SCHEMA_VERSION}"
        }
        val generatedFrom = section(document, GENERATED_FROM)
        return BenchmarkConfig(
            generatedFrom = GeneratedFrom(
                capture = string(generatedFrom, CAPTURE),
                trial = string(generatedFrom, TRIAL),
                device = LinkedHashMap(section(generatedFrom, DEVICE)),
            ),
            run = runEntry(section(document, RUN)),
            providers = section(document, PROVIDERS).mapValuesTo(LinkedHashMap()) { (provider, types) ->
                asSection(types, provider).mapValuesTo(LinkedHashMap()) { (type, entries) ->
                    asSection(entries, "$provider.$type").mapValuesTo(LinkedHashMap()) { (name, entry) ->
                        entryOf(asSection(entry, "$provider.$type.$name"))
                    }
                }
            },
            schemaVersion = schemaVersion,
        )
    }

    private fun runDocument(run: RunSettings): Map<String, Any> = linkedMapOf(
        INPUT_SIZES to run.inputSizes,
        PHASES to run.phases,
        METRICS to run.metrics,
        PROCESS_REPETITIONS to run.processRepetitions,
        SEED to run.seed,
    )

    private fun runEntry(document: Map<String, Any>): RunSettings = RunSettings(
        inputSizes = numbers(document, INPUT_SIZES),
        phases = strings(document, PHASES),
        metrics = strings(document, METRICS),
        processRepetitions = number(document, PROCESS_REPETITIONS).toInt(),
        seed = number(document, SEED).toLong(),
    )

    private fun entryDocument(entry: ConfigEntry): Map<String, Any> {
        val document = linkedMapOf<String, Any>(ENABLED to entry.enabled)
        if (entry.keySizes.isNotEmpty()) document[KEY_SIZES] = entry.keySizes
        if (entry.inputSizes.isNotEmpty()) document[INPUT_SIZES] = entry.inputSizes
        if (entry.key.isNotEmpty()) document[KEY] = LinkedHashMap(entry.key)
        if (entry.parameters.isNotEmpty()) document[PARAMETERS] = LinkedHashMap(entry.parameters)
        if (entry.keyAlgorithm.isNotEmpty()) document[KEY_ALGORITHM] = entry.keyAlgorithm
        if (entry.keyProvider.isNotEmpty()) document[KEY_PROVIDER] = entry.keyProvider
        if (entry.providerChose.isNotEmpty()) document[PROVIDER_CHOSE] = entry.providerChose
        if (entry.bareName) document[BARE_NAME] = true
        if (entry.reason.isNotEmpty()) document[REASON] = entry.reason
        return document
    }

    private fun entryOf(document: Map<String, Any>): ConfigEntry = ConfigEntry(
        enabled = boolean(document, ENABLED),
        keySizes = optionalNumbers(document, KEY_SIZES),
        inputSizes = optionalNumbers(document, INPUT_SIZES),
        key = optionalSection(document, KEY) ?: emptyMap(),
        parameters = optionalSection(document, PARAMETERS) ?: emptyMap(),
        keyAlgorithm = optionalString(document, KEY_ALGORITHM),
        keyProvider = optionalString(document, KEY_PROVIDER),
        providerChose = optionalString(document, PROVIDER_CHOSE),
        bareName = optionalBoolean(document, BARE_NAME),
        reason = optionalString(document, REASON),
    )
}
