package io.github.junekim0007.cryptobench.config.effective

import io.github.junekim0007.cryptobench.settings.EngineRows
import io.github.junekim0007.cryptobench.settings.StoppedOnFailureException
import io.github.junekim0007.cryptobench.settings.OnFailure
import io.github.junekim0007.cryptobench.config.effective.dto.EffectiveConfig
import io.github.junekim0007.cryptobench.config.effective.dto.EffectiveEntry
import io.github.junekim0007.cryptobench.config.effective.dto.EffectiveSource
import io.github.junekim0007.cryptobench.config.effective.dto.EntryOrigin
import io.github.junekim0007.cryptobench.settings.Skip
import io.github.junekim0007.cryptobench.config.entry.EngineCatalog
import io.github.junekim0007.cryptobench.config.entry.KeySource
import io.github.junekim0007.cryptobench.config.entry.Variants
import io.github.junekim0007.cryptobench.config.global.dto.GlobalConfig
import io.github.junekim0007.cryptobench.config.global.dto.Policy
import io.github.junekim0007.cryptobench.config.testset.dto.Override
import io.github.junekim0007.cryptobench.config.testset.dto.Rule
import io.github.junekim0007.cryptobench.config.testset.dto.TestSet
import io.github.junekim0007.cryptobench.config.inventory.dto.Inventory
import io.github.junekim0007.cryptobench.files.VariantLabels
import io.github.junekim0007.cryptobench.settings.Facts
import io.github.junekim0007.cryptobench.settings.HarnessSettings
import io.github.junekim0007.cryptobench.settings.Unsupported

class EffectiveBuilder {

    fun build(global: GlobalConfig, testSet: TestSet, inventory: Inventory, files: Files, facts: Facts = Facts.UNKNOWN): EffectiveConfig {
        val (runHarness, runUnsupported) = checkedRun(global, facts)
        val all = inventory.entries()
        val included = if (testSet.include.isEmpty()) all else all.filter { located -> testSet.include.any { it.rule.matches(located) } }
        val excludes = testSet.exclude + global.selection.exclude
        val selected = included.filter { located -> excludes.none { it.matches(located) } }
        val resolver = OverrideResolver(testSet.overrides, testSet.include)
        val groups = selected.associateWith { located -> runnableGroups(testSet, located, resolver, global.run.variants) }.filterValues { it.isNotEmpty() }
        val skipped = configSkips(testSet, all, selected, groups)
        stopOnSkips(global.policy, skipped)
        val entries = entries(groups, resolver, global.run.variants, runHarness, facts, inventory) { located, group -> origin(testSet, files.testSet, located, group) }
        stopOnSkips(global.policy, skipped + entries.skips)
        val (warmup, warmupWarnings) = WarmupJobs.resolve(global.run.warmup, entries.providers)
        return EffectiveConfig(
            generatedFrom = EffectiveSource(files.global, files.testSet, files.inventory, inventory.generatedFrom),
            run = global.run.copy(harness = runHarness, warmup = warmup),
            policy = global.policy,
            providers = entries.providers,
            skipped = skipped + entries.skips,
            warnings = inventory.warnings + global.notices + testSet.notices + warnings(excludes, included, testSet.overrides, groups) +
                runUnsupported.map { it.toString() } + entries.warnings + warmupWarnings +
                entries.dropped.map { (typePath, count) -> VariantLabels.notApplicable("${typePath.first} ($count ${if (count == 1) "entry" else "entries"})",
                    EngineCatalog.rows.applicable(typePath.first), listOf(typePath.second)) } +
                listOfNotNull(entries.secureAsked.takeIf { it > 0 }?.let { Variants.secureUnavailable("$it entries") }) +
                ShadowedSettings.of(global, testSet),
            analysis = global.analysis,
            bundledProviders = global.providers.bundled,
        )
    }

    private fun checkedRun(global: GlobalConfig, facts: Facts): Pair<HarnessSettings, List<Unsupported>> {
        val (runHarness, runUnsupported) = HARNESS.forDevice(global.run.harness, facts, RUN_HARNESS)
        runUnsupported.firstOrNull { it.required }?.let { throw IllegalArgumentException(it.toString()) }
        return runHarness to runUnsupported
    }

    private fun configSkips(testSet: TestSet, all: List<Inventory.Located>, selected: List<Inventory.Located>,
                            groups: Map<Inventory.Located, List<String?>>): List<Skip> =
        testSet.include.map { it.rule }
            .filter { rule -> all.none { rule.matches(it) } }
            .map { rule -> Skip(Skip.CONFIG, rule.provider, rule.type, rule.name, "no_match: nothing on this device matches the include") } +
            selected.filter { !it.entry.runs && groups[it]?.size != groupsOf(testSet, it).size }.map { Skip(Skip.CONFIG, it.provider, it.type, it.name, "not_runnable: ${it.entry.reason}") }

    // a generator the default-run trial cannot call (its key is born inside the provider) runs only in the groups that ask secure
    private fun runnableGroups(testSet: TestSet, located: Inventory.Located, resolver: OverrideResolver, runVariants: List<String>): List<String?> {
        val names = groupsOf(testSet, located)
        if (located.entry.runs) return names
        if (Variants.SECURE !in EngineCatalog.rows.applicable(located.type)) return emptyList()
        return names.filter { Variants.SECURE in resolver.resolve(located, it).variants.ifEmpty { runVariants } }
    }

    private fun stopOnSkips(policy: Policy, skips: List<Skip>) {
        if (skips.isNotEmpty() && policy.onFailure == OnFailure.STOP) {
            throw StoppedOnFailureException(skips)
        }
    }

    private fun warnings(excludes: List<Rule>, included: List<Inventory.Located>, overrides: List<Override>,
                         groups: Map<Inventory.Located, List<String?>>): List<String> =
        excludes.filter { rule -> included.none { rule.matches(it) } }.map { "exclude_matches_nothing: $it" } +
            overrides
                .filter { override -> groups.none { (located, names) -> override.match.matches(located) && names.any { override.match.appliesTo(it) } } }
                .map { "override_matches_nothing: ${it.match}" }

    private fun entries(groups: Map<Inventory.Located, List<String?>>, resolver: OverrideResolver, runVariants: List<String>, runHarness: HarnessSettings,
                        facts: Facts, inventory: Inventory, origin: (Inventory.Located, String?) -> EntryOrigin): Entries {
        val entries = Entries()
        for ((located, names) in groups) {
            for (group in names) {
                val key = entryKey(located.name, group)
                val path = "${located.provider}.${located.type}.$key.harness"
                val entry = resolver.resolve(located, group)
                // an entry records only the variants it asked for; without them the run's apply
                val asked = entry.variants.ifEmpty { runVariants }
                val runnable = Variants.runnable(asked, located.type)
                val variants = if (located.entry.runs) Variants.runnable(entry.variants, located.type) else listOf(Variants.SECURE)
                val refusal = KeySource.refusal(entry.key, located, inventory) ?: runnable.takeIf { it.isEmpty() }?.let { notRunnable(located, key, asked) }
                if (refusal != null) {
                    entries.skips += Skip(Skip.CONFIG, located.provider, located.type, key, refusal)
                    continue
                }
                // a secure-only entry: each size or curve the keystore trial refused is a config skip with the trial's code, never prepared
                val checked = if (variants == listOf(Variants.SECURE)) KeystoreRefusals.of(entry, located, inventory) else null
                checked?.refusals?.forEach { entries.skips += Skip(Skip.CONFIG, located.provider, located.type, key, it) }
                if (checked?.whole == true) continue
                for (dropped in asked - runnable.toSet()) {
                    if (dropped == Variants.SECURE) entries.secureAsked++
                    else entries.dropped.merge(located.type to dropped, 1, Int::plus)
                }
                val unsupported = HARNESS.unsupported(runHarness.mergedWith(entry.harness), facts, path)
                unsupported.firstOrNull { it.required }?.let {
                    entries.skips += Skip(Skip.CONFIG, located.provider, located.type, key, it.toString())
                    continue
                }
                entries.warnings += unsupported.map { fallback(it, path, runHarness) }
                entries.providers.getOrPut(located.provider) { LinkedHashMap() }
                    .getOrPut(located.type) { LinkedHashMap() }[key] = entry.copy(keySizes = checked?.keySizes ?: entry.keySizes, variants = variants, key = KeySource.spelled(entry.key, inventory), harness = HARNESS.honoured(entry.harness, unsupported, facts, path),
                        from = origin(located, group))
            }
        }
        return entries
    }

    private class Entries {
        val providers = LinkedHashMap<String, LinkedHashMap<String, LinkedHashMap<String, EffectiveEntry>>>()
        val skips = mutableListOf<Skip>()
        val warnings = mutableListOf<String>()
        val dropped = LinkedHashMap<Pair<String, String>, Int>()
        var secureAsked = 0
    }

    private fun notRunnable(located: Inventory.Located, key: String, asked: List<String>): String {
        val subject = "${located.provider}.${located.type}.$key"
        if (EngineCatalog.rows.row(located.type) == null) return EngineRows.notInCatalogue(located.type)
        val applies = EngineCatalog.rows.applicable(located.type)
        val dropped = asked - applies.toSet()
        return if (dropped == listOf(Variants.SECURE) && applies.isNotEmpty()) Variants.secureUnavailable("$subject alone")
            else VariantLabels.notApplicable(subject, applies, dropped)
    }

    /** One device entry is measured once per group the test set names, and once as itself when no include names a group. */
    private fun groupsOf(testSet: TestSet, located: Inventory.Located): List<String?> {
        if (testSet.include.isEmpty()) {
            return listOf(null)
        }
        return testSet.include.map { it.rule }.filter { it.matches(located) }.map { it.group }.distinct()
    }

    // selection is a union: every include that gives this entry its group selected it; none wins
    private fun origin(testSet: TestSet, file: String, located: Inventory.Located, group: String?): EntryOrigin = EntryOrigin(file,
        testSet.include.withIndex().filter { (_, include) -> include.rule.matches(located) && include.rule.group == group }.associate { (index, include) -> index to include.rule })

    private fun entryKey(name: String, group: String?): String = if (group == null) name else "$name@$group"

    data class Files(val global: String, val testSet: String, val inventory: String)

    /** An entry's dropped key leaves the run's value in force; the warning says which. */
    private fun fallback(unsupported: Unsupported, path: String, run: HarnessSettings): String {
        val key = unsupported.path.removePrefix("$path.").substringBefore('.')
        return if (key in HarnessSettings.write(run)) "$unsupported; $RUN_HARNESS.$key applies" else unsupported.toString()
    }

    private companion object {
        const val RUN_HARNESS = "run.harness"
        val HARNESS = HarnessSettings.HARNESS
    }
}
