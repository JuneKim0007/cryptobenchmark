package io.github.junekim0007.cryptobench.benchmark

import io.github.junekim0007.cryptobench.benchmark.check.PlanCheck
import io.github.junekim0007.cryptobench.benchmark.run.HostHarness
import io.github.junekim0007.cryptobench.benchmark.check.Refusal
import io.github.junekim0007.cryptobench.settings.HarnessSettings
import io.github.junekim0007.cryptobench.settings.Metric
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import org.junit.Assert.assertEquals
import org.junit.Test

class PlanCheckTest {

    private val installed = { setOf("SUN", "SunJCE") }

    private fun case(
        algorithm: String = "SHA-256",
        provider: String = "SUN",
        operation: Operation = Operation.DIGEST,
        inputSize: Int? = 1024,
        harness: HarnessSettings = HarnessSettings(),
        metrics: Set<Metric> = setOf(Metric.TIME),
    ) = BenchmarkCase("MessageDigest", algorithm, provider, operation, inputSize = inputSize, metrics = metrics, harness = harness)

    private class Run(val cases: List<BenchmarkCase>, val processRepetitions: Int)

    private fun run(vararg cases: BenchmarkCase, processRepetitions: Int = 1) = Run(cases.toList(), processRepetitions)

    private fun PlanCheck.check(run: Run) = check(run.cases, run.processRepetitions)

    private fun PlanCheck.runnable(run: Run) = runnable(run.cases, run.processRepetitions)

    @Test
    fun aPlanThisDeviceCanRunIsAccepted() {
        assertEquals(emptyList<Refusal>(), PlanCheck(HostHarness.METRICS, installed).check(run(case())))
    }

    @Test
    fun aMetricTheHarnessCannotMeasureIsRefused() {
        val refusal = PlanCheck(HostHarness.METRICS, installed).check(run(case(metrics = setOf(Metric.TIME, Metric.ALLOCATION)))).single()
        assertEquals("not_supported", refusal.reason.substringBefore(':'))
    }

    @Test
    fun namesWhatItWillNotRun() {
        val refusals = PlanCheck(HostHarness.METRICS, installed).check(run(
            case(provider = "BC"),
            case(algorithm = "SHA-512", operation = Operation.TYPE_DEFAULT),
        ))
        assertEquals(listOf("provider_not_installed", "not_measurable"), refusals.map { it.reason.substringBefore(':') })
    }

    @Test
    fun oneRefusedCaseIsLeftOutWithItsReasonAndTheOthersRun() {
        val checked = PlanCheck(HostHarness.METRICS, installed).runnable(run(case(provider = "BC"), case(), case(algorithm = "SHA-512")))
        assertEquals(listOf("MessageDigest_SHA-256_DIGEST_SUN_i1024_WARM_fixed", "MessageDigest_SHA-512_DIGEST_SUN_i1024_WARM_fixed"),
            checked.runnable.map { it.id })
        assertEquals(listOf("MessageDigest_SHA-256_DIGEST_BC_i1024_WARM_fixed" to "provider_not_installed"),
            checked.refused.map { (case, refusal) -> case.id to refusal.reason.substringBefore(':') })
    }

    @Test
    fun noRunnableCaseOrARunWideRefusalStillRefusesThePlan() {
        val check = PlanCheck(HostHarness.METRICS, installed)
        org.junit.Assert.assertThrows(RefusedPlanException::class.java) { check.runnable(run(case(provider = "BC"))) }
        org.junit.Assert.assertThrows(RefusedPlanException::class.java) { check.runnable(run(case(), processRepetitions = 0)) }
    }

    @Test
    fun anEmptyPlanIsRefusedBeforeAnyTimerStarts() {
        assertEquals(listOf("nothing_to_measure"), PlanCheck(HostHarness.METRICS, installed).check(run()).map { it.toString() })
    }

    @Test
    fun twoCasesCannotShareAnId() {
        assertEquals(listOf("duplicate_case"), PlanCheck(HostHarness.METRICS, installed).check(run(case(), case())).map { it.reason.substringBefore(':') })
    }
}
