package io.github.junekim0007.cryptobench.benchmark.verify.oracle

import io.github.junekim0007.cryptobench.benchmark.run.OneCall
import io.github.junekim0007.cryptobench.benchmark.run.OutputHook
import io.github.junekim0007.cryptobench.benchmark.verify.OutputBytes
import io.github.junekim0007.cryptobench.benchmark.verify.known.KnownAnswer
import io.github.junekim0007.cryptobench.benchmark.verify.known.RawMaterial
import io.github.junekim0007.cryptobench.preparation.interop.report.Outcome
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.operation.Invocations
import io.github.junekim0007.cryptobench.preparation.parameter.bind.BindException
import java.security.InvalidAlgorithmParameterException
import java.security.InvalidKeyException
import java.security.spec.InvalidKeySpecException
import javax.crypto.Cipher

/** The case's own invocation over a vector's raw key, fixed parameters and input, through the case's one-call path (HostHarness.ONCE, or the Jetpack dry run on a device); its output against the source. */
class KnownAnswerOracle(private val vectors: List<KnownAnswer>, private val call: OneCall) : Oracle {

    override val name = "knownAnswer"

    override fun judge(call: CheckedCall): Judgement {
        val case = call.prepared.case
        val vector = vectors.firstOrNull { it.matches(case) } ?: return Judgement(Outcome.NotCheckable("no_vector: ${case.type}.${case.algorithm} ${case.operation}"))
        val cited = mapOf("vector" to vector.id, "source" to vector.source)
        val hook = OutputHook()
        val invocation = try {
            Invocations.of(RawMaterial.of(vector, call.prepared)).also { this.call.call(it, hook) }
        } catch (refused: Exception) {
            val root = refused.cause ?: refused
            val outcome = if (refused is BindException || refused is InvalidKeyException || root is InvalidKeyException || root is InvalidKeySpecException || root is InvalidAlgorithmParameterException) {
                Outcome.NotCheckable("raw_material_refused: ${root.javaClass.simpleName}: ${root.message}")
            } else Outcome.Fail("call_failed: ${root.javaClass.simpleName}: ${root.message}")
            return Judgement(outcome, cited)
        }
        val fixed = vector.parameters?.let { RawMaterial.fixedBytes(it) }.orEmpty()
        val used = (invocation.engine as? Cipher)?.iv
        if (used != null && fixed.isNotEmpty() && fixed.none { it.contentEquals(used) }) return Judgement(Outcome.Fail("vector_iv_not_used"), cited)
        if (case.operation == Operation.VERIFY) return Judgement(Outcome.Pass, cited)
        val expected = if (case.operation == Operation.DECRYPT) vector.input else vector.output
        val got = OutputBytes.of(hook.outputs.lastOrNull()) ?: return Judgement(Outcome.Fail("no_bytes: the call returned ${hook.outputs.lastOrNull()?.javaClass?.simpleName}"), cited)
        val compared = if (vector.prefixOnly && got.size >= expected.size) got.copyOf(expected.size) else got
        return Judgement(if (compared.contentEquals(expected)) Outcome.Pass else Outcome.Fail("output_differs: ${got.size} bytes, the source gives ${expected.size}"), cited)
    }
}
