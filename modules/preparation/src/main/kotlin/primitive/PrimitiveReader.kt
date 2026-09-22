package io.github.junekim0007.cryptobench.preparation.primitive

import io.github.junekim0007.cryptobench.preparation.global.GlobalSettings
import io.github.junekim0007.cryptobench.preparation.inbound.InboundDocument
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.request.Selection
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields.asSection
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields.choice
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields.optionalNumbers
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields.optionalSection
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields.optionalStrings

object PrimitiveReader {

    fun read(inbound: InboundDocument, global: GlobalSettings): List<Selection> {
        val selections = inbound.providers.flatMap { (provider, types) ->
            asSection(types, provider).flatMap { (type, entries) ->
                asSection(entries, "$provider.$type").map { (key, value) -> selection(provider, type, key, asSection(value, "$provider.$type.$key"), global) }
            }
        }
        require(selections.isNotEmpty()) { "nothing_selected: ${inbound.fileName}" }
        return selections
    }

    private fun selection(provider: String, type: String, key: String, entry: Map<String, Any>, global: GlobalSettings) = Selection(
        type = type,
        algorithm = key.substringBefore('@'),
        group = key.substringAfter('@', missingDelimiterValue = ""),
        providers = listOf(provider),
        keySizes = optionalNumbers(entry, "keySizes"),
        inputSizes = global.inputSizesFor(optionalNumbers(entry, "inputSizes")),
        keyParameters = optionalSection(entry, "key"),
        parameters = optionalSection(entry, "parameters"),
        operations = optionalStrings(entry, "operations").mapTo(LinkedHashSet()) { choice<Operation>("operation", it) },
    )
}
