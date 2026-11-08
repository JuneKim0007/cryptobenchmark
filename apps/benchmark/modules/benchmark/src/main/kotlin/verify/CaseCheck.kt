package io.github.junekim0007.cryptobench.benchmark.verify

import io.github.junekim0007.cryptobench.benchmark.run.OneCall
import io.github.junekim0007.cryptobench.benchmark.run.OutputHook
import io.github.junekim0007.cryptobench.benchmark.verify.known.KnownAnswer
import io.github.junekim0007.cryptobench.benchmark.verify.observe.ObservedCall
import io.github.junekim0007.cryptobench.benchmark.verify.oracle.CheckedCall
import io.github.junekim0007.cryptobench.benchmark.verify.oracle.ContractOracle
import io.github.junekim0007.cryptobench.benchmark.verify.oracle.CrossProviderOracle
import io.github.junekim0007.cryptobench.benchmark.verify.oracle.Judgement
import io.github.junekim0007.cryptobench.benchmark.verify.oracle.KnownAnswerOracle
import io.github.junekim0007.cryptobench.benchmark.verify.oracle.NonceOracle
import io.github.junekim0007.cryptobench.benchmark.verify.oracle.Oracle
import io.github.junekim0007.cryptobench.benchmark.verify.oracle.PlanOracle
import io.github.junekim0007.cryptobench.benchmark.verify.record.CaseRecord
import io.github.junekim0007.cryptobench.jca.failure.Attempt
import io.github.junekim0007.cryptobench.preparation.interop.report.Outcome
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.operation.Invocations
import io.github.junekim0007.cryptobench.preparation.port.DeviceCapability
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import io.github.junekim0007.cryptobench.preparation.shared.FailureText

/** One case end to end: the timed path's invocation, one harness call into the hook, what it did, then every oracle over its output.
 * The check path's only catch site, by the one rule (Attempt): an Exception or LinkageError is this case's error or verdict; any other Error escapes to the orchestrator. */
class CaseCheck(private val oracles: List<Oracle>, private val call: OneCall) {

    fun check(prepared: PreparedCase): CaseRecord {
        val invocation = Attempt.of { Invocations.of(prepared) }
            .getOrElse { failure -> return CaseRecord.of(prepared, emptyMap(), emptyMap(), "invocation_failed: ${FailureText.of(failure)}", null) }
        val observed = ObservedCall.start(prepared, invocation)
        val hook = OutputHook()
        val thrown = Attempt.of { call.call(invocation, hook) }.exceptionOrNull()
        val observation = observed.finish(hook.outputs.size)
        if (thrown != null) return CaseRecord.of(prepared, observation.record, emptyMap(), "call_failed: ${FailureText.of(thrown)}", null)
        val checked = CheckedCall(prepared, invocation, hook.outputs.last())
        val judgements = linkedMapOf(PlanOracle.NAME to PlanOracle.judge(observation, invocation.perCall), NonceOracle.NAME to NonceOracle.judge(observation, prepared))
        for (oracle in oracles) {
            judgements[oracle.name] = Attempt.of { oracle.judge(checked) }
                .getOrElse { Judgement(Outcome.Fail("oracle_failed: ${FailureText.of(it)}")) }
        }
        return CaseRecord.of(prepared, observation.record, judgements, null, deterministicDigest(prepared, checked))
    }

    // Keyless and equal on a second call: the bytes depend only on the seeded input, so the digest is comparable across runs.
    private fun deterministicDigest(prepared: PreparedCase, checked: CheckedCall): String? {
        if (prepared.key != KeyMaterial.None) return null
        val first = OutputBytes.of(checked.output) ?: return null
        val again = Attempt.of { OutputBytes.of(checked.invocation.once()) }.getOrNull()
        return if (first.contentEquals(again)) OutputBytes.digest(first) else null
    }

    companion object {

        // Strongest first; the known answer's call takes the case's own one-call path, so give both the same call.
        fun oracles(vectors: List<KnownAnswer>, capability: DeviceCapability, call: OneCall): List<Oracle> =
            listOf(KnownAnswerOracle(vectors, call), CrossProviderOracle(capability), ContractOracle())
    }
}
