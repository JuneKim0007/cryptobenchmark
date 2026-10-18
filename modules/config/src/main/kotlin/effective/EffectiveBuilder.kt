package io.github.junekim0007.cryptobench.config.effective

import io.github.junekim0007.cryptobench.config.effective.dto.EffectiveConfig
import io.github.junekim0007.cryptobench.config.effective.dto.EffectiveEntry
import io.github.junekim0007.cryptobench.config.effective.dto.EffectiveSource
import io.github.junekim0007.cryptobench.config.effective.dto.Skip
import io.github.junekim0007.cryptobench.config.global.dto.GlobalConfig
import io.github.junekim0007.cryptobench.config.global.dto.Policy
import io.github.junekim0007.cryptobench.config.testset.dto.TestSet
import io.github.junekim0007.cryptobench.config.inventory.dto.Inventory
import io.github.junekim0007.cryptobench.settings.Facts
import io.github.junekim0007.cryptobench.settings.HarnessSettings

class EffectiveBuilder {

    fun build(global: GlobalConfig, testSet: TestSet, inventory: Inventory, files: Files, facts: Facts = Facts.UNKNOWN): EffectiveConfig {
        val runUnsupported = HARNESS.unsupported(global.run.harness, facts, RUN_HARNESS)
        runUnsupported.firstOrNull { it.required }?.let { throw IllegalArgumentException(it.toString()) }
        val run = global.run.copy(harness = HARNESS.supported(global.run.harness, runUnsupported, RUN_HARNESS))
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
        val entrySkips = mutableListOf<Skip>()
        val entryWarnings = mutableListOf<String>()
        for ((located, names) in groups) {
            for (group in names) {
                val key = entryKey(located.name, group)
                val path = "${located.provider}.${located.type}.$key.harness"
                val entry = resolver.resolve(located, group)
                val unsupported = HARNESS.unsupported(entry.harness, facts, path)
                unsupported.firstOrNull { it.required }?.let {
                    entrySkips += Skip(Skip.CONFIG, located.provider, located.type, key, it.toString())
                    continue
                }
                entryWarnings += unsupported.map { it.toString() }
                providers.getOrPut(located.provider) { LinkedHashMap() }
                    .getOrPut(located.type) { LinkedHashMap() }[key] = entry.copy(harness = HARNESS.supported(entry.harness, unsupported, path))
            }
        }
        if (entrySkips.isNotEmpty() && global.policy.onFailure == Policy.OnFailure.STOP) {
            throw StoppedOnFailureException(skipped + entrySkips)
        }
        return EffectiveConfig(
            generatedFrom = EffectiveSource(files.global, files.testSet, files.inventory, inventory.generatedFrom),
            run = run,
            policy = global.policy,
            providers = providers,
            skipped = skipped + entrySkips,
            warnings = warnings + runUnsupported.map { it.toString() } + entryWarnings,
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

    private companion object {
        const val RUN_HARNESS = "run.harness"
        val HARNESS = HarnessSettings.HARNESS
    }
}
