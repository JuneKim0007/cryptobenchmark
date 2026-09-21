package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.config.effective.EffectiveBuilder
import io.github.junekim0007.cryptobench.config.effective.UnavailableSelectionException
import io.github.junekim0007.cryptobench.config.global.GlobalDocument
import io.github.junekim0007.cryptobench.config.global.dto.Policy
import io.github.junekim0007.cryptobench.config.inventory.InventoryBuilder
import io.github.junekim0007.cryptobench.config.source.CaptureSource
import io.github.junekim0007.cryptobench.config.source.TrialSource
import io.github.junekim0007.cryptobench.config.testset.TestSetDocument
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
    }

    /** An include that matches nothing on this device is reported, not silently dropped. */
    @Test
    fun whatCannotRunIsSkippedWithAReason() {
        assertEquals(listOf("* Mac HmacSHA256: no_match: nothing on this device matches the include"), effective.skipped.map { it.toString() })
    }

    @Test
    fun aNotRunnableSelectionIsReported() {
        val withoutGlobalExclude = global.copy(selection = global.selection.copy(exclude = emptyList()))
        val skipped = EffectiveBuilder().build(withoutGlobalExclude, testSet, inventory, names).skipped.map { it.toString() }
        assertTrue(skipped.toString(), skipped.contains("SunJCE KeyGenerator SunTlsPrf: not_runnable: IllegalStateException: TlsPrfGenerator must be initialized"))
    }

    @Test
    fun failPolicyStopsAndListsEverySkip() {
        val strict = global.copy(policy = Policy(Policy.OnUnavailable.FAIL))
        val error = assertThrows(UnavailableSelectionException::class.java) { EffectiveBuilder().build(strict, testSet, inventory, names) }
        assertEquals(1, error.skipped.size)
    }

    @Test
    fun nothingSelectedIsAnError() {
        val excludeAll = global.copy(selection = global.selection.copy(exclude = listOf(Rule(type = "Cipher"), Rule(type = "MessageDigest"))))
        assertEquals("nothing_selected", assertThrows(IllegalArgumentException::class.java) { EffectiveBuilder().build(excludeAll, testSet, inventory, names) }.message)
    }

    @Test
    fun theInputsAreRecorded() {
        assertEquals("testsets/scope.yaml", effective.generatedFrom.testSet)
        assertEquals("probe_x.yaml", effective.generatedFrom.capture)
        assertEquals(2, effective.run.processRepetitions)
    }
}
