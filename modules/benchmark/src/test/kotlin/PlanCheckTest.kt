package io.github.junekim0007.cryptobench.benchmark

import io.github.junekim0007.cryptobench.benchmark.check.PlanCheck
import io.github.junekim0007.cryptobench.benchmark.check.Refusal
import io.github.junekim0007.cryptobench.preparation.global.HarnessSettings
import io.github.junekim0007.cryptobench.preparation.input.OperationInput
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyRecipe
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedRun
import org.junit.Assert.assertEquals
import org.junit.Test

/**
 * A plan is checked against the device that will run it, not the one that wrote it: the file may
 * have been prepared on a host, pushed to a phone, and the provider it names may not be there.
 */
class PlanCheckTest {

    private val installed = { setOf("SUN", "SunJCE") }

    private fun case(
        algorithm: String = "SHA-256",
        provider: String = "SUN",
        operation: Operation = Operation.DIGEST,
        inputSize: Int? = 1024,
        harness: HarnessSettings = HarnessSettings(),
    ) = PreparedCase(
        BenchmarkCase("MessageDigest", algorithm, provider, operation, inputSize = inputSize, harness = harness),
        KeyRecipe.None,
        KeyMaterial.None,
        null,
        null,
        OperationInput.Message(ByteArray(inputSize ?: 0)),
    )

    private fun run(vararg cases: PreparedCase, processRepetitions: Int = 1) =
        PreparedRun(cases.toList(), emptyList(), processRepetitions)

    @Test
    fun aPlanThisDeviceCanRunIsAccepted() {
        assertEquals(emptyList<Refusal>(), PlanCheck(installed).check(run(case())))
    }

    @Test
    fun namesWhatItWillNotRun() {
        val refusals = PlanCheck(installed).check(run(
            case(provider = "BC"),
            case(algorithm = "SHA-512", operation = Operation.TYPE_DEFAULT),
        ))
        assertEquals(
            listOf(
                "MessageDigest_SHA-256_DIGEST_BC_i1024_WARM: provider_not_installed: BC, installed [SUN, SunJCE]",
                "MessageDigest_SHA-512_TYPE-DEFAULT_SUN_i1024_WARM: not_measurable: MessageDigest has no operation this harness can time",
            ),
            refusals.map { it.toString() },
        )
    }

    @Test
    fun anEmptyPlanIsRefusedBeforeAnyTimerStarts() {
        assertEquals(listOf("nothing_to_measure"), PlanCheck(installed).check(run()).map { it.toString() })
    }

    /** Two cases with one id would overwrite each other in the results: the run stops instead. */
    @Test
    fun twoCasesCannotShareAnId() {
        assertEquals(
            listOf("MessageDigest_SHA-256_DIGEST_SUN_i1024_WARM: duplicate_case: 2 cases share this id"),
            PlanCheck(installed).check(run(case(), case())).map { it.toString() },
        )
    }

    /** A measured case is only dropped, so one impossible case does not cost the whole run. */
    @Test
    fun theRefusedCasesAreTheOnlyOnesLeftUnmeasured() {
        val measured = mutableListOf<String>()
        val benchmark = Benchmark(PlanCheck(installed), onRefusal = {})
        benchmark.measure(run(case(), case(algorithm = "SHA-512", provider = "BC"))) { prepared ->
            measured += prepared.case.id
            io.github.junekim0007.cryptobench.benchmark.run.CaseMeasurement(prepared.case, 1, listOf(1L))
        }
        assertEquals(listOf("MessageDigest_SHA-256_DIGEST_SUN_i1024_WARM"), measured)
    }
}
