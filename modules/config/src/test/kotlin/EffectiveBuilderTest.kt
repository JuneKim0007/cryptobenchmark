package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.config.effective.EffectiveBuilder
import io.github.junekim0007.cryptobench.config.effective.StoppedOnFailureException
import io.github.junekim0007.cryptobench.config.global.GlobalDocument
import io.github.junekim0007.cryptobench.config.global.dto.Policy
import io.github.junekim0007.cryptobench.config.inventory.InventoryBuilder
import io.github.junekim0007.cryptobench.config.source.CaptureSource
import io.github.junekim0007.cryptobench.config.source.TrialSource
import io.github.junekim0007.cryptobench.config.testset.TestSetDocument
import io.github.junekim0007.cryptobench.config.testset.dto.Override
import io.github.junekim0007.cryptobench.config.testset.dto.Rule
import io.github.junekim0007.cryptobench.config.yaml.YamlFiles
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test

class EffectiveBuilderTest {

    private val files = YamlFiles()
    private val inventory = InventoryBuilder().build(
        CaptureSource.parse(files.load(Fixtures.CAPTURE)),
        TrialSource.parse(files.load(Fixtures.TRIAL)),
        InventoryBuilder.Files("probe_x.yaml", "trial_x.yaml"),
    )
    private val global = GlobalDocument.parse(files.load(Fixtures.GLOBAL))
    private val testSet = TestSetDocument.parse(files.load(Fixtures.TEST_SET))
    private val names = EffectiveBuilder.Files("global.yaml", "testsets/scope.yaml", "inventory.yaml")

    private val effective = EffectiveBuilder().build(global, testSet, inventory, names)

    /** include → test-set exclude (bare AES) → global exclude (every KeyGenerator). */
    @Test
    fun includeThenBothExcludes() {
        assertEquals(mapOf("SunJCE" to setOf("AES/CBC/PKCS5PADDING", "RSA"), "SUN" to setOf("SHA-256")),
            effective.providers.mapValues { (_, types) -> types.values.flatMap { it.keys }.toSet() })
    }

    @Test
    fun overridesResolvePerEntry() {
        val cipher = effective.providers.getValue("SunJCE").getValue("Cipher")
        assertEquals(listOf(128, 256), cipher.getValue("AES/CBC/PKCS5PADDING").keySizes)
        assertEquals("javax.crypto.spec.IvParameterSpec", cipher.getValue("AES/CBC/PKCS5PADDING").parameters["class"])
        assertEquals(listOf(128), cipher.getValue("RSA").keySizes)
        assertEquals(listOf(32), cipher.getValue("RSA").inputSizes)
        assertEquals(listOf("ENCRYPT"), cipher.getValue("RSA").operations)
    }

    /** An include that matches nothing on this device is reported, not silently dropped. */
    @Test
    fun whatCannotRunIsSkippedWithAReason() {
        assertEquals(listOf("[config] * Mac HmacSHA256: no_match: nothing on this device matches the include"), effective.skipped.map { it.toString() })
    }

    @Test
    fun aNotRunnableSelectionIsReported() {
        val withoutGlobalExclude = global.copy(selection = global.selection.copy(exclude = emptyList()))
        val skipped = EffectiveBuilder().build(withoutGlobalExclude, testSet, inventory, names).skipped.map { it.toString() }
        assertTrue(skipped.toString(), skipped.contains("[config] SunJCE KeyGenerator SunTlsPrf: not_runnable: IllegalStateException: TlsPrfGenerator must be initialized"))
    }

    @Test
    fun stopPolicyStopsAndListsEveryFailure() {
        val strict = global.copy(policy = Policy(Policy.OnFailure.STOP))
        val error = assertThrows(StoppedOnFailureException::class.java) { EffectiveBuilder().build(strict, testSet, inventory, names) }
        assertEquals(1, error.skipped.size)
    }

    /** Later stages apply the same rule, so it travels in the file they read. */
    @Test
    fun thePolicyIsFrozenIntoTheResult() {
        assertEquals(Policy.OnFailure.SKIP, effective.policy.onFailure)
    }

    @Test
    fun nothingSelectedIsAnError() {
        val excludeAll = global.copy(selection = global.selection.copy(exclude = listOf(Rule(type = "Cipher"), Rule(type = "MessageDigest"))))
        assertEquals("nothing_selected", assertThrows(IllegalArgumentException::class.java) { EffectiveBuilder().build(excludeAll, testSet, inventory, names) }.message)
    }

    @Test
    fun theInputsAreRecorded() {
        assertEquals("testsets/scope.yaml", effective.generatedFrom.testSet)
        assertEquals("probe_x.yaml", effective.generatedFrom.environment.capture)
        assertEquals(2, effective.run.processRepetitions)
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
}
