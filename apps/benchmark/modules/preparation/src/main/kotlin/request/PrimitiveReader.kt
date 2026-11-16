package io.github.junekim0007.cryptobench.preparation.request

import io.github.junekim0007.cryptobench.settings.HarnessSettings
import io.github.junekim0007.cryptobench.preparation.inbound.InboundDocument
import io.github.junekim0007.cryptobench.preparation.key.plan.KeySource
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.measurement.Variant
import io.github.junekim0007.cryptobench.document.DocumentFields.asSection
import io.github.junekim0007.cryptobench.document.DocumentFields.choice
import io.github.junekim0007.cryptobench.document.DocumentFields.expectKeys
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalNumbers
import io.github.junekim0007.cryptobench.document.DocumentFields.sectionOrEmpty
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalStrings

object PrimitiveReader {

    private val ENTRY_KEYS = listOf("keySizes", "inputSizes", "key", "parameters", "operations", "variants", "providerDefaults", "harness")

    fun read(inbound: InboundDocument): List<Selection> {
        val selections = inbound.providers.flatMap { (provider, types) ->
            asSection(types, provider).flatMap { (type, entries) ->
                asSection(entries, "$provider.$type").map { (key, value) -> selection(provider, type, key, asSection(value, "$provider.$type.$key")) }
            }
        }
        require(selections.isNotEmpty()) { "nothing_selected: ${inbound.fileName}" }
        return selections
    }

    private fun selection(provider: String, type: String, key: String, entry: Map<String, Any>): Selection {
        expectKeys(entry, ENTRY_KEYS, "$provider.$type.$key")
        val (keySource, keySpec) = KeySource.split(sectionOrEmpty(entry, "key"), "$provider.$type.$key.key")
        return Selection(
            type = type,
            algorithm = key.substringBefore('@'),
            group = key.substringAfter('@', missingDelimiterValue = ""),
            provider = provider,
            keySizes = optionalNumbers(entry, "keySizes"),
            inputSizes = optionalNumbers(entry, "inputSizes"),
            keyParameters = keySpec,
            keySource = keySource,
            parameters = sectionOrEmpty(entry, "parameters"),
            operations = optionalStrings(entry, "operations").mapTo(LinkedHashSet()) { choice<Operation>("operation", it) },
            harness = HarnessSettings.read(sectionOrEmpty(entry, "harness"), "$provider.$type.$key.harness"),
            variants = if ("variants" in entry) optionalStrings(entry, "variants").map(Variant::of) else null,
        )
    }
}
