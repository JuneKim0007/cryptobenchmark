package io.github.junekim0007.cryptobench.config.effective

import io.github.junekim0007.cryptobench.config.effective.dto.EffectiveEntry
import io.github.junekim0007.cryptobench.config.entry.KeySource
import io.github.junekim0007.cryptobench.settings.HarnessSettings
import io.github.junekim0007.cryptobench.config.testset.dto.Include
import io.github.junekim0007.cryptobench.config.testset.dto.Override
import io.github.junekim0007.cryptobench.config.testset.dto.Rule
import io.github.junekim0007.cryptobench.config.inventory.dto.Inventory
import io.github.junekim0007.cryptobench.document.names.AlgorithmNames

/** variants: an override's set, else an include's, else none (the run's applies); within each the most specific, then the later, wins. */
internal class OverrideResolver(private val names: AlgorithmNames, private val overrides: List<Override>, private val includes: List<Include> = emptyList()) {

    fun resolve(located: Inventory.Located, group: String?): EffectiveEntry {
        val applicable = applicable(overrides, Override::match, located, group)
        val keySizes = applicable.lastOrNull { it.keySizes != null }?.keySizes
        val inputSizes = applicable.lastOrNull { it.inputSizes != null }?.inputSizes
        val key = applicable.lastOrNull { it.key != null }?.key.orEmpty()
        val parameters = applicable.lastOrNull { it.parameters != null }?.parameters.orEmpty()
        val operations = applicable.lastOrNull { it.operations != null }?.operations.orEmpty()
        val variants = applicable.lastOrNull { it.variants != null }?.variants
            ?: applicable(includes, Include::rule, located, group).lastOrNull { it.variants != null }?.variants.orEmpty()
        val harness = applicable.fold(HarnessSettings()) { merged, override -> merged.mergedWith(override.harness) }
        val observed = located.entry
        return EffectiveEntry(
            keySizes = keySizes.orEmpty(),
            inputSizes = inputSizes ?: observed.inputSizes,
            key = key,
            parameters = parameters,
            operations = operations,
            variants = variants,
            harness = harness,
            providerDefaults = listOfNotNull(
                // a key source alone names no size: only a spec tree replaces the provider's default size
                "keySize".takeIf { keySizes == null && key.keys.all { it in KeySource.KEYS } && observed.keySizes.isNotEmpty() },
                "parameters".takeIf { parameters.isEmpty() && observed.providerChose.isNotEmpty() },
                "modeAndPadding".takeIf { observed.bareName },
            ),
        )
    }

    private fun <T> applicable(items: List<T>, rule: (T) -> Rule, located: Inventory.Located, group: String?): List<T> = items
        .withIndex()
        .filter { (_, item) -> rule(item).matches(names, located) && rule(item).appliesTo(group) }
        .sortedWith(compareBy({ rule(it.value).specificity }, { it.index }))
        .map { it.value }
}
