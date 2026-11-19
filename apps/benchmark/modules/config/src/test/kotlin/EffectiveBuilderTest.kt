package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.settings.OnFailure
import io.github.junekim0007.cryptobench.config.effective.EffectiveBuilder
import io.github.junekim0007.cryptobench.settings.StoppedOnFailureException
import io.github.junekim0007.cryptobench.config.global.GlobalDocument
import io.github.junekim0007.cryptobench.config.global.dto.Policy
import io.github.junekim0007.cryptobench.config.global.dto.Warmup
import io.github.junekim0007.cryptobench.config.inventory.InventoryBuilder
import io.github.junekim0007.cryptobench.config.source.CaptureSource
import io.github.junekim0007.cryptobench.config.source.TrialSource
import io.github.junekim0007.cryptobench.config.testset.TestSetDocument
import io.github.junekim0007.cryptobench.config.testset.dto.Include
import io.github.junekim0007.cryptobench.config.testset.dto.Override
import io.github.junekim0007.cryptobench.config.testset.dto.Rule
import io.github.junekim0007.cryptobench.config.testset.dto.TestSet
import io.github.junekim0007.cryptobench.config.yaml.YamlFiles
import io.github.junekim0007.cryptobench.document.YamlCodec
import io.github.junekim0007.cryptobench.settings.CoreChoice
import io.github.junekim0007.cryptobench.settings.CpuSettings
import io.github.junekim0007.cryptobench.settings.Facts
import io.github.junekim0007.cryptobench.settings.HarnessSettings
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test

class EffectiveBuilderTest {

    private val files = YamlFiles()
    private val codec = YamlCodec.DOCUMENT
    private val inventory = InventoryBuilder().build(
        CaptureSource.parse(codec.load(Fixtures.CAPTURE)),
        TrialSource.parse(codec.load(Fixtures.TRIAL)),
        InventoryBuilder.Files("probe_x.yaml", "trial_x.yaml"),
    )
    private val global = GlobalDocument.parse(codec.load(Fixtures.GLOBAL))
    private val testSet = TestSetDocument.parse(codec.load(Fixtures.TEST_SET))
    private val names = EffectiveBuilder.Files("global.yaml", "testsets/default_predefined.yaml", "inventory.yaml")

    private val effective = EffectiveBuilder().build(global, testSet, inventory, names)

    /** include → test-set exclude (bare AES) → global exclude (every KeyGenerator). */
    @Test
    fun includeThenBothExcludes() {
        assertEquals(mapOf("SunJCE" to setOf("AES/CBC/PKCS5PADDING", "RSA"), "SUN" to setOf("SHA-256")),
            effective.providers.mapValues { (_, types) -> types.values.flatMap { it.keys }.toSet() })
    }

    /** An include that matches nothing on this device is reported, not silently dropped. */
    @Test
    fun whatCannotRunIsSkippedWithAReason() {
        assertEquals(listOf("no_match"), effective.skipped.map { it.code })
    }

    @Test
    fun aNotRunnableSelectionIsReported() {
        val withoutGlobalExclude = global.copy(selection = global.selection.copy(exclude = emptyList()))
        val skipped = EffectiveBuilder().build(withoutGlobalExclude, testSet, inventory, names).skipped.map { it.toString() }
        assertTrue(skipped.toString(), skipped.any { "SunTlsPrf: not_runnable:" in it })
    }

    @Test
    fun stopPolicyStopsAndListsEveryFailure() {
        val strict = global.copy(policy = Policy(OnFailure.STOP))
        val error = assertThrows(StoppedOnFailureException::class.java) { EffectiveBuilder().build(strict, testSet, inventory, names) }
        assertEquals(1, error.skipped.size)
    }

    @Test
    fun nothingSelectedIsAnError() {
        val excludeAll = global.copy(selection = global.selection.copy(exclude = listOf(Rule(type = "Cipher"), Rule(type = "MessageDigest"))))
        assertEquals("nothing_selected", assertThrows(IllegalArgumentException::class.java) { EffectiveBuilder().build(excludeAll, testSet, inventory, names) }.message)
    }

    /** A misspelt override silently changes what is measured, so every rule that touched nothing is reported. */
    @Test
    fun rulesThatMatchNothingAreWarnedAbout() {
        assertEquals(emptyList<String>(), effective.warnings)
        val typos = testSet.copy(
            exclude = testSet.exclude + Rule(name = "SHA-265"),
            overrides = testSet.overrides + Override(Rule(type = "Cipher", name = "AES/GCM/NoPaddng"), keySizes = listOf(256)),
        )
        assertEquals(
            listOf("exclude_matches_nothing: {name=SHA-265}", "override_matches_nothing: {type=Cipher name=AES/GCM/NoPaddng}"),
            EffectiveBuilder().build(global, typos, inventory, names).warnings,
        )
    }

    @Test
    fun whatTheInventoryLeftOutIsWarnedAboutFirst() {
        val noted = inventory.copy(warnings = listOf("duplicate_name: P.Cipher A and B are one name; B left out"))
        assertEquals(listOf("duplicate_name: P.Cipher A and B are one name; B left out"),
            EffectiveBuilder().build(global, testSet, noted, names).warnings)
    }

    /** A group is the same device entry measured again under another name, so it is one entry per group. */
    @Test
    fun anIncludeGroupMakesItsOwnEntry() {
        val grouped = TestSet(
            description = "one primitive, two groups",
            include = listOf(
                Include(Rule(type = "Cipher", name = "AES/CBC/PKCS5PADDING", group = "pkcs5")),
                Include(Rule(type = "Cipher", name = "AES/CBC/PKCS5PADDING", group = "sized")),
            ),
            overrides = listOf(Override(Rule(type = "Cipher", name = "AES/CBC/PKCS5PADDING", group = "sized"), keySizes = listOf(128))),
        )
        val effective = EffectiveBuilder().build(global, grouped, inventory, names)
        val entries = effective.providers.getValue("SunJCE").getValue("Cipher")
        assertEquals(listOf("AES/CBC/PKCS5PADDING@pkcs5", "AES/CBC/PKCS5PADDING@sized"), entries.keys.toList())
        assertEquals(emptyList<Int>(), entries.getValue("AES/CBC/PKCS5PADDING@pkcs5").keySizes)
        assertEquals(listOf(128), entries.getValue("AES/CBC/PKCS5PADDING@sized").keySizes)
    }

    /** Selection is a union: every include that took this entry's group is recorded, by its index in the test set; none wins. */
    @Test
    fun anEntryRecordsEveryIncludeThatSelectedIt() {
        val overlapping = TestSet(
            description = "two includes select one entry, a third names a group",
            include = listOf(
                Include(Rule(type = "Cipher", name = "AES*")),
                Include(Rule(type = "Cipher", name = "AES/CBC/PKCS5PADDING", group = "sized")),
                Include(Rule(provider = "SunJCE", type = "Cipher", name = "AES/CBC/PKCS5PADDING")),
            ),
        )
        val entries = EffectiveBuilder().build(global, overlapping, inventory, names).providers.getValue("SunJCE").getValue("Cipher")
        val origin = { key: String -> entries.getValue(key).from!! }
        assertEquals("testsets/default_predefined.yaml", origin("AES/CBC/PKCS5PADDING").testSet)
        assertEquals(listOf(0, 2), origin("AES/CBC/PKCS5PADDING").includes.keys.toList())
        assertEquals(overlapping.include[2].rule, origin("AES/CBC/PKCS5PADDING").includes[2])
        assertEquals(listOf(1), origin("AES/CBC/PKCS5PADDING@sized").includes.keys.toList())
        val everything = EffectiveBuilder().build(global, TestSet(description = "no include"), inventory, names)
        assertEquals(setOf(emptyMap<Int, Rule>()), everything.providers.values.flatMap { types -> types.values.flatMap { it.values } }.map { it.from!!.includes }.toSet())
    }

    private val pinnable = Facts(true, 37, listOf(Facts.Core(0, true, 2_000_000), Facts.Core(7, true, 3_800_000)), true)

    private fun withRunCpu(cpu: CpuSettings) = global.copy(run = global.run.copy(harness = global.run.harness.copy(cpu = cpu)))

    private fun entryCpu(cpu: CpuSettings) = testSet.copy(overrides = testSet.overrides + Override(Rule(type = "MessageDigest"), harness = HarnessSettings(cpu = cpu)))

    @Test
    fun aSupportedSettingIsKeptWithBigResolvedToACore() {
        assertEquals(CpuSettings(CoreChoice.Index(7)), EffectiveBuilder().build(withRunCpu(CpuSettings(CoreChoice.Big)), testSet, inventory, names, pinnable).run.harness.cpu)
    }

    @Test
    fun anEntryIsCheckedWithTheRunValuesItInherits() {
        val built = EffectiveBuilder().build(withRunCpu(CpuSettings(CoreChoice.Big, required = true)), entryCpu(CpuSettings(CoreChoice.Index(5))), inventory, names, pinnable)
        assertTrue(built.skipped.toString(), built.skipped.any { it.type == "MessageDigest" && it.reason.contains("no_core: core 5") && it.reason.endsWith("(required)") })
    }

    @Test
    fun aDroppedEntryValueSaysTheRunValueApplies() {
        val built = EffectiveBuilder().build(withRunCpu(CpuSettings(CoreChoice.Big)), entryCpu(CpuSettings(CoreChoice.Index(5))), inventory, names, pinnable)
        assertTrue(built.warnings.toString(), built.warnings.any { it.contains(".cpu: no_core: core 5") && it.endsWith("; run.harness.cpu applies") })
    }

    @Test
    fun anUnsupportedRunSettingIsRemovedWithAWarning() {
        val built = EffectiveBuilder().build(withRunCpu(CpuSettings(CoreChoice.Big)), testSet, inventory, names)
        assertNull(built.run.harness.cpu)
        assertTrue(built.warnings.toString(), built.warnings.any { it.startsWith("not_supported: run.harness.cpu: facts_unknown:") })
    }

    @Test
    fun anUnsupportedRequiredRunSettingStopsTheConfig() {
        val failure = assertThrows(IllegalArgumentException::class.java) {
            EffectiveBuilder().build(withRunCpu(CpuSettings(CoreChoice.Index(9), required = true)), testSet, inventory, names, pinnable)
        }
        assertTrue(failure.message!!.startsWith("not_supported: run.harness.cpu: no_core:"))
    }

    @Test
    fun anUnsupportedRequiredEntrySettingSkipsOnlyThoseEntries() {
        val built = EffectiveBuilder().build(global, entryCpu(CpuSettings(CoreChoice.Big, required = true)), inventory, names, pinnable.copy(pinning = false))
        assertTrue(built.skipped.toString(), built.skipped.any { it.type == "MessageDigest" && it.reason.contains("no_pinning") })
        assertTrue(built.providers.values.none { it.containsKey("MessageDigest") })
    }

    /** The effective run carries the warm-up resolved against its own entries, and the warnings of that resolution. */
    @Test
    fun theWarmupIsResolvedAgainstTheSelectedEntries() {
        val built = EffectiveBuilder().build(global.copy(run = global.run.copy(warmup = Warmup(10, listOf(Rule(name = "SHA-256"), Rule(name = "Nothing"))))), testSet, inventory, names)
        assertEquals(Warmup(10, listOf(Rule("SUN", "MessageDigest", "SHA-256"))), built.run.warmup)
        assertTrue(built.warnings.toString(), "warmup_job_matches_nothing: {name=Nothing}" in built.warnings)
    }

    @Test
    fun anUnknownMetricIsRefusedAtConfigTime() {
        val failure = assertThrows(IllegalArgumentException::class.java) { global.run.copy(metrics = listOf("TIME", "NOT_A_METRIC")) }
        assertEquals("invalid: run.metrics NOT_A_METRIC, known [TIME, ALLOCATION]", failure.message)
    }
}
