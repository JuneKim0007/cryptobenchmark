package io.github.junekim0007.cryptobench.benchmark

import io.github.junekim0007.cryptobench.benchmark.run.HostHarness
import io.github.junekim0007.cryptobench.benchmark.run.OneCall
import io.github.junekim0007.cryptobench.benchmark.verify.known.KnownAnswer
import io.github.junekim0007.cryptobench.benchmark.verify.known.KnownAnswerFile
import io.github.junekim0007.cryptobench.benchmark.verify.oracle.CheckedCall
import io.github.junekim0007.cryptobench.benchmark.verify.oracle.KnownAnswerOracle
import io.github.junekim0007.cryptobench.preparation.input.OperationInput
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyRecipe
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.operation.Invocations
import io.github.junekim0007.cryptobench.preparation.peer.Outcome
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import org.junit.Assert.assertEquals
import org.junit.Test
import java.security.KeyPairGenerator

/** A verify known answer passes only when the call's verdict is the source's: a valid signature verifies. */
class KnownAnswerVerifyTest {

    private val vector = KnownAnswerFile.read(CheckFixture.knownAnswers).single { it.id == "ed25519-rfc8032-test2" }

    // byte 32 is S's lowest: still a well-formed signature, which the provider answers false
    private val tampered = with(vector) {
        KnownAnswer(id, source, type, algorithms, operations, key, parameters, input, output.copyOf().also { it[32] = (it[32].toInt() xor 1).toByte() }, prefixOnly)
    }

    private val prepared = KeyPairGenerator.getInstance("Ed25519", "SunEC").generateKeyPair().let { pair ->
        PreparedCase(
            BenchmarkCase("Signature", "Ed25519", "SunEC", Operation.VERIFY, inputSize = 1),
            KeyRecipe.Pair("Ed25519", null, "SunEC"), KeyMaterial.Pairs(listOf(pair)), null, null,
            OperationInput.SignedMessage(byteArrayOf(0x72), ByteArray(64), null),
        )
    }

    private fun judged(call: OneCall, with: KnownAnswer = vector): Outcome =
        KnownAnswerOracle(listOf(with), call).judge(CheckedCall(prepared, Invocations.of(prepared), null)).outcome

    @Test
    fun theSourcesSignatureVerifies() {
        assertEquals(Outcome.Pass, judged(HostHarness.ONCE))
    }

    @Test
    fun aSignatureWithOneFlippedByteFails() {
        assertEquals(Outcome.Fail("call_failed: IllegalStateException: verify_failed"), judged(HostHarness.ONCE, tampered))
    }

    @Test
    fun aCallThatReturnsFalseWithoutThrowingFails() {
        assertEquals(Outcome.Fail("verify_verdict_differs: the call returned false, the source gives true"), judged(OneCall { invocation, hook -> invocation.once(); hook.consume(false) }))
    }

    @Test
    fun aCallThatReturnsNoVerdictFails() {
        assertEquals(Outcome.Fail("verify_verdict_differs: the call returned null, the source gives true"), judged(OneCall { invocation, hook -> invocation.once(); hook.consume(null) }))
    }
}
