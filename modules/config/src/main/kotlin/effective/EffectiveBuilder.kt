package io.github.junekim0007.cryptobench.config.effective

import io.github.junekim0007.cryptobench.config.effective.dto.EffectiveConfig
import io.github.junekim0007.cryptobench.config.effective.dto.EffectiveEntry
import io.github.junekim0007.cryptobench.config.effective.dto.EffectiveSource
import io.github.junekim0007.cryptobench.config.effective.dto.Skip
import io.github.junekim0007.cryptobench.config.global.dto.GlobalConfig
import io.github.junekim0007.cryptobench.config.global.dto.Policy
import io.github.junekim0007.cryptobench.config.testset.dto.TestSet
import io.github.junekim0007.cryptobench.config.inventory.dto.Inventory

class EffectiveBuilder {

    fun build(global: GlobalConfig, testSet: TestSet, inventory: Inventory, files: Files): EffectiveConfig {
        val all = inventory.entries()
        val included = if (testSet.include.isEmpty()) all else all.filter { located -> testSet.include.any { it.matches(located) } }
        val excludes = testSet.exclude + global.selection.exclude
        val selected = included.filter { located -> excludes.none { it.matches(located) } }

        val skipped = testSet.include
            .filter { rule -> all.none { rule.matches(it) } }
            .map { rule -> Skip(Skip.CONFIG, rule.provider, rule.type, rule.name, "no_match: nothing on this device matches the include") } +
            selected.filter { !it.entry.runs }.map { Skip(Skip.CONFIG, it.provider, it.type, it.name, "not_runnable: ${it.entry.reason}") }

        if (skipped.isNotEmpty() && global.policy.onFailure == Policy.OnFailure.STOP) {
            throw StoppedOnFailureException(skipped)
        }

        val running = selected.filter { it.entry.runs }
        val groups = running.associateWith { located -> groupsOf(testSet, located) }
        val warnings = excludes.filter { rule -> included.none { rule.matches(it) } }.map { "exclude_matches_nothing: $it" } +
            testSet.overrides
                .filter { override -> groups.none { (located, names) -> override.match.matches(located) && names.any { override.match.appliesTo(it) } } }
                .map { "override_matches_nothing: ${it.match}" }

        val resolver = OverrideResolver(testSet.overrides)
        val providers = LinkedHashMap<String, LinkedHashMap<String, LinkedHashMap<String, EffectiveEntry>>>()
        for ((located, names) in groups) {
            for (group in names) {
                providers.getOrPut(located.provider) { LinkedHashMap() }
                    .getOrPut(located.type) { LinkedHashMap() }[entryKey(located.name, group)] = resolver.resolve(located, group)
            }
        }
        return EffectiveConfig(
            generatedFrom = EffectiveSource(files.global, files.testSet, files.inventory, inventory.generatedFrom),
            run = global.run,
            policy = global.policy,
            providers = providers,
            skipped = skipped,
            warnings = warnings,
        )
    }

    /** One device entry is measured once per group the test set names, and once as itself when no include names a group. */
    private fun groupsOf(testSet: TestSet, located: Inventory.Located): List<String?> {
        if (testSet.include.isEmpty()) {
            return listOf(null)
        }
        return testSet.include.filter { it.matches(located) }.map { it.group }.distinct()
    }

    private fun entryKey(name: String, group: String?): String = if (group == null) name else "$name@$group"

    data class Files(val global: String, val testSet: String, val inventory: String)
}
