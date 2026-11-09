package io.github.junekim0007.cryptobench.benchmark

import io.github.junekim0007.cryptobench.benchmark.check.PlanCheck
import io.github.junekim0007.cryptobench.benchmark.check.RunnablePlan
import io.github.junekim0007.cryptobench.benchmark.run.HostHarness
import io.github.junekim0007.cryptobench.preparation.Preparation
import io.github.junekim0007.cryptobench.preparation.port.Availability
import io.github.junekim0007.cryptobench.preparation.port.DeviceCapability
import io.github.junekim0007.cryptobench.preparation.prepare.StoppedOnFailureException
import io.github.junekim0007.cryptobench.preparation.report.Skip
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
import java.io.File
import java.security.Security

/** The orchestrator loses only the failing case: any throw at preparation is that case's logged skip, and both files say so. */
class RunnablePlanTest {

    @get:Rule
    val folder = TemporaryFolder()

    private val logged = mutableListOf<Skip>()

    private val device = object : DeviceCapability {
        override fun providers() = listOf("SUN", ThrowingProvider.NAME)
        override fun check(provider: String, type: String, algorithm: String): Availability =
            if (provider == ThrowingProvider.NAME || algorithm == "SHA-256") Availability.Available else Availability.Unavailable("not_registered")
    }

    private fun effective(onFailure: String = "skip", extra: String = "") = File(folder.root, "effective.yaml").apply {
        writeText("""
schemaVersion: 1
generatedFrom: {global: g, testSet: t, inventory: i, capture: c, trial: t, device: {}}
run: {inputSizes: [64], phases: [WARM], metrics: [TIME], processRepetitions: 1, seed: 0, variants: [fixed]}
policy: {onFailure: $onFailure}
providers:
  SUN:
    MessageDigest:
      SHA-256: {}$extra
  ${ThrowingProvider.NAME}:
    MessageDigest:
      ${ThrowingProvider.ASSERTION}: {}
      ${ThrowingProvider.OVERFLOW}: {}
      ${ThrowingProvider.EXCEPTION}: {}
skipped: []
""".trimIndent())
    }

    private val plan get() = RunnablePlan(Preparation(device), PlanCheck(HostHarness.METRICS), File(folder.root, "out")) { logged += it }

    @Before
    fun install() {
        Security.addProvider(ThrowingProvider())
        ThrowingProvider.armed = true
    }

    @After
    fun remove() {
        ThrowingProvider.armed = false
        Security.removeProvider(ThrowingProvider.NAME)
    }

    @Test
    fun anyThrowAtPreparationLosesOnlyItsCase() {
        val prepared = plan.preparedAll(effective())
        assertEquals(listOf("MessageDigest_SHA-256_DIGEST_SUN_i64_WARM_fixed"), prepared.map { it.case.id })
        val reasons = logged.map { it.reason.substringAfter(": ") }
        assertEquals(listOf("preparation_failed: AssertionError", "preparation_failed: StackOverflowError", "dry_run_failed: IllegalStateException"),
            reasons.map { it.substringBefore(": armed").substringBefore(": null").trimEnd(':', ' ') })
        val skipped = File(folder.root, "out/skipped.yaml").readText()
        assertTrue(skipped, logged.all { it.name!! in skipped })
        val record = File(folder.root, "out/prepared.yaml").readText()
        assertTrue(record, "SHA-256" in record && ThrowingProvider.ASSERTION !in record)
    }

    @Test
    fun aLaterStageFailureIsTheCasesSkipToo() {
        ThrowingProvider.armed = false
        val plan = plan
        val prepared = plan.preparedAll(effective())
        ThrowingProvider.armed = true
        val measured = prepared.mapNotNull { case -> plan.guarded(case.case, RunnablePlan.BENCHMARK, RunnablePlan.MEASURE_FAILED) { HostHarness(1_000_000, 1_000_000, 2, collectionCount = { 0L }).measure(case) } }
        assertEquals(listOf("SHA-256"), measured.map { it.case.algorithm })
        assertEquals(3, logged.count { it.stage == RunnablePlan.BENCHMARK && "measure_failed" in it.reason })
    }

    @Test
    fun runningOutOfMemoryDuringTheCheckRecordsTheCaseThenStops() {
        val plan = plan
        val case = plan.list(effective(), written = true).first()
        assertEquals(null, plan.guarded<Unit>(case, RunnablePlan.CHECK, RunnablePlan.CHECK_FAILED) { throw OutOfMemoryError("native") })
        assertEquals(RunnablePlan.CHECK, plan.skipped.last().stage)
        assertThrows(OutOfMemoryError::class.java) { plan.guarded(case, RunnablePlan.CHECK, RunnablePlan.CHECK_FAILED) { } }
    }

    @Test
    fun stopListsEveryFailureAndStillWritesTheReport() {
        val error = assertThrows(StoppedOnFailureException::class.java) { plan.preparedAll(effective("stop", "\n      SHA-512: {}")) }
        assertEquals(4, error.skipped.size)
        assertTrue(File(folder.root, "out/skipped.yaml").readText().contains("not_registered"))
    }
}
