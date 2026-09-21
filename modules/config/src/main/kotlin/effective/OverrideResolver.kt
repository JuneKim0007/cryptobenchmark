package io.github.junekim0007.cryptobench.config.effective

import io.github.junekim0007.cryptobench.config.effective.dto.EffectiveEntry
import io.github.junekim0007.cryptobench.config.testset.dto.Override
import io.github.junekim0007.cryptobench.config.inventory.dto.Inventory

internal class OverrideResolver(private val overrides: List<Override>) {

    fun resolve(located: Inventory.Located): EffectiveEntry {
        val applicable = overrides
            .withIndex()
            .filter { (_, override) -> override.match.matches(located) }
            .sortedWith(compareBy({ it.value.match.specificity }, { it.index }))
            .map { it.value }
        val keySizes = applicable.lastOrNull { it.keySizes != null }?.keySizes
        val inputSizes = applicable.lastOrNull { it.inputSizes != null }?.inputSizes
        val key = applicable.lastOrNull { it.key != null }?.key.orEmpty()
        val parameters = applicable.lastOrNull { it.parameters != null }?.parameters.orEmpty()
        val observed = located.entry
        return EffectiveEntry(
            keySizes = keySizes.orEmpty(),
            inputSizes = inputSizes ?: observed.inputSizes,
            key = key,
            parameters = parameters,
            providerDefaults = listOfNotNull(
                "keySize".takeIf { keySizes == null && key.isEmpty() && observed.keySizes.isNotEmpty() },
                "parameters".takeIf { parameters.isEmpty() && observed.providerChose.isNotEmpty() },
                "modeAndPadding".takeIf { observed.bareName },
            ),
        )
    }
}
