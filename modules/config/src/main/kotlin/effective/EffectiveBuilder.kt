package io.github.junekim0007.cryptobench.config.effective

import io.github.junekim0007.cryptobench.config.effective.dto.EffectiveConfig
import io.github.junekim0007.cryptobench.config.effective.dto.EffectiveEntry
import io.github.junekim0007.cryptobench.config.effective.dto.EffectiveSource
import io.github.junekim0007.cryptobench.config.effective.dto.Skip
import io.github.junekim0007.cryptobench.config.global.dto.GlobalConfig
import io.github.junekim0007.cryptobench.config.global.dto.Policy
import io.github.junekim0007.cryptobench.config.testset.dto.Rule
import io.github.junekim0007.cryptobench.config.testset.dto.TestSet
import io.github.junekim0007.cryptobench.config.inventory.dto.Inventory

/**
 * global × test set × inventory → what will run:
 * include (empty = everything) → drop excludes, test set's then global's → resolve overrides → apply policy.
 */
class EffectiveBuilder {

    fun build(global: GlobalConfig, testSet: TestSet, inventory: Inventory, files: Files): EffectiveConfig {
        val all = inventory.entries()
        val included = if (testSet.include.isEmpty()) all else all.filter { located -> testSet.include.any { it.matches(located) } }
        val excludes = testSet.exclude + global.selection.exclude
        val selected = included.filter { located -> excludes.none { it.matches(located) } }

        val skipped = testSet.include
            .filter { rule -> all.none { rule.matches(it) } }
            .map { rule -> Skip(rule.provider, rule.type, rule.name, "no_match: nothing on this device matches the include") } +
            selected.filter { !it.entry.runs }.map { Skip(it.provider, it.type, it.name, "not_runnable: ${it.entry.reason}") }

        if (skipped.isNotEmpty() && global.policy.onUnavailable == Policy.OnUnavailable.FAIL) {
            throw UnavailableSelectionException(skipped)
        }

        val resolver = OverrideResolver(testSet.overrides)
        val providers = LinkedHashMap<String, LinkedHashMap<String, LinkedHashMap<String, EffectiveEntry>>>()
        for (located in selected.filter { it.entry.runs }) {
            providers.getOrPut(located.provider) { LinkedHashMap() }
                .getOrPut(located.type) { LinkedHashMap() }[located.name] = resolver.resolve(located)
        }
        return EffectiveConfig(
            generatedFrom = EffectiveSource(
                global = files.global,
                testSet = files.testSet,
                inventory = files.inventory,
                capture = inventory.generatedFrom.capture,
                trial = inventory.generatedFrom.trial,
                device = inventory.generatedFrom.device,
            ),
            run = global.run,
            providers = providers,
            skipped = skipped,
        )
    }

    /** Names of the authored and generated files, recorded in the result. */
    data class Files(val global: String, val testSet: String, val inventory: String)

    private fun Rule.matches(located: Inventory.Located): Boolean =
        matches(located.provider, located.type, located.name)
}
