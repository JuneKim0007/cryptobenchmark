import io.github.junekim0007.cryptobench.benchmark.run.OneCall
import io.github.junekim0007.cryptobench.benchmark.verify.known.KnownAnswer
import io.github.junekim0007.cryptobench.benchmark.verify.oracle.CheckedCall
import io.github.junekim0007.cryptobench.benchmark.verify.oracle.KnownAnswerOracle
import io.github.junekim0007.cryptobench.benchmark.verify.oracle.cross.PeerRefusal
import io.github.junekim0007.cryptobench.benchmark.verify.oracle.cross.PeerRun
import io.github.junekim0007.cryptobench.preparation.input.InputBytes
import io.github.junekim0007.cryptobench.preparation.input.OperationInput
import io.github.junekim0007.cryptobench.preparation.interop.check.CrossCheck
import io.github.junekim0007.cryptobench.preparation.peer.Outcome
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyRecipe
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.operation.Invocations
import io.github.junekim0007.cryptobench.preparation.parameter.bind.BindException
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import org.junit.Assert.assertEquals
import org.junit.Test
import java.security.GeneralSecurityException
import java.security.InvalidAlgorithmParameterException
import java.security.InvalidKeyException
import java.security.NoSuchAlgorithmException
import java.security.SignatureException
import java.security.spec.InvalidKeySpecException
import javax.crypto.BadPaddingException
import javax.crypto.IllegalBlockSizeException
import javax.crypto.NoSuchPaddingException

/** Characterization: one exception, four entry points that classify it (interop CrossCheck, cross-provider setup and judge, known answer); today's codes. */
class FailureClassifiersTest {

    private val thrown: List<Exception> = listOf(
        InvalidKeyException("m"), InvalidAlgorithmParameterException("m"), ClassCastException("m"),
        BadPaddingException("m"), IllegalBlockSizeException("m"), SignatureException("m"),
        IllegalStateException("verify_failed"), IllegalStateException("m"), NoSuchAlgorithmException("m"), NoSuchPaddingException("m"),
        InvalidKeySpecException("m"), GeneralSecurityException("m"), BindException("p", "m"), PeerRefusal("peer_code", "m"), RuntimeException("m"),
    )

    private val prepared = PreparedCase(
        BenchmarkCase("MessageDigest", "SHA-256", "SUN", Operation.DIGEST, inputSize = 3),
        KeyRecipe.None, KeyMaterial.None, null, null, OperationInput.Message(InputBytes.of(0, 3)),
    )
    private val vector = KnownAnswer("v", "s", "MessageDigest", listOf("SHA-256"), setOf(Operation.DIGEST), null, null,
        byteArrayOf(0x61, 0x62, 0x63), ByteArray(32), prefixOnly = false)

    private fun shown(outcome: Outcome): String = when (outcome) {
        Outcome.Pass -> "pass"
        is Outcome.Fail -> "fail ${outcome.reason}"
        is Outcome.NotCheckable -> "not_checkable ${outcome.reason}"
    }

    private fun knownAnswer(failure: Exception): Outcome =
        KnownAnswerOracle(listOf(vector), OneCall { _, _ -> throw failure })
            .judge(CheckedCall(prepared, Invocations.of(prepared), null)).outcome

    @Test
    fun todayEachEntryPointCodesTheSameExceptionItsOwnWay() {
        val table = thrown.joinToString("\n") { failure ->
            listOf(
                failure.javaClass.simpleName,
                shown(CrossCheck.classify(failure)),
                shown(PeerRun.of<Unit>({ throw failure }) { Outcome.Pass }),
                shown(PeerRun.of({ Unit }) { throw failure }),
                shown(knownAnswer(failure)),
            ).joinToString(" | ")
        }
        assertEquals(EXPECTED, table)
    }

    private companion object {
        // exception | CrossCheck.classify | PeerRun setup | PeerRun judge | KnownAnswerOracle
        val EXPECTED = """
            InvalidKeyException | not_checkable key_or_parameters_rejected: InvalidKeyException: m | not_checkable peer_key_rejected: InvalidKeyException: m | fail peer_refused: InvalidKeyException: m | not_checkable raw_material_refused: InvalidKeyException: m
            InvalidAlgorithmParameterException | not_checkable key_or_parameters_rejected: InvalidAlgorithmParameterException: m | not_checkable peer_parameters_rejected: InvalidAlgorithmParameterException: m | fail peer_refused: InvalidAlgorithmParameterException: m | not_checkable raw_material_refused: InvalidAlgorithmParameterException: m
            ClassCastException | not_checkable key_or_parameters_rejected: ClassCastException: m | not_checkable peer_setup_failed: ClassCastException: m | not_checkable peer_error: ClassCastException: m | fail call_failed: ClassCastException: m
            BadPaddingException | fail BadPaddingException: m | not_checkable peer_setup_failed: BadPaddingException: m | fail peer_refused: BadPaddingException: m | fail call_failed: BadPaddingException: m
            IllegalBlockSizeException | fail IllegalBlockSizeException: m | not_checkable peer_setup_failed: IllegalBlockSizeException: m | fail peer_refused: IllegalBlockSizeException: m | fail call_failed: IllegalBlockSizeException: m
            SignatureException | fail SignatureException: m | not_checkable peer_setup_failed: SignatureException: m | fail peer_refused: SignatureException: m | fail call_failed: SignatureException: m
            IllegalStateException | fail IllegalStateException: verify_failed | not_checkable peer_setup_failed: IllegalStateException: verify_failed | not_checkable peer_error: IllegalStateException: verify_failed | fail call_failed: IllegalStateException: verify_failed
            IllegalStateException | not_checkable error: IllegalStateException: m | not_checkable peer_setup_failed: IllegalStateException: m | not_checkable peer_error: IllegalStateException: m | fail call_failed: IllegalStateException: m
            NoSuchAlgorithmException | not_checkable error: NoSuchAlgorithmException: m | not_checkable peer_unavailable: NoSuchAlgorithmException: m | fail peer_refused: NoSuchAlgorithmException: m | fail call_failed: NoSuchAlgorithmException: m
            NoSuchPaddingException | not_checkable error: NoSuchPaddingException: m | not_checkable peer_unavailable: NoSuchPaddingException: m | fail peer_refused: NoSuchPaddingException: m | fail call_failed: NoSuchPaddingException: m
            InvalidKeySpecException | not_checkable error: InvalidKeySpecException: m | not_checkable peer_setup_failed: InvalidKeySpecException: m | fail peer_refused: InvalidKeySpecException: m | not_checkable raw_material_refused: InvalidKeySpecException: m
            GeneralSecurityException | not_checkable error: GeneralSecurityException: m | not_checkable peer_setup_failed: GeneralSecurityException: m | fail peer_refused: GeneralSecurityException: m | fail call_failed: GeneralSecurityException: m
            BindException | not_checkable error: BindException: bind_failed: p: m | not_checkable peer_setup_failed: BindException: bind_failed: p: m | not_checkable peer_error: BindException: bind_failed: p: m | not_checkable raw_material_refused: BindException: bind_failed: p: m
            PeerRefusal | not_checkable error: PeerRefusal: m | not_checkable peer_code: m | not_checkable peer_error: PeerRefusal: m | fail call_failed: PeerRefusal: m
            RuntimeException | not_checkable error: RuntimeException: m | not_checkable peer_setup_failed: RuntimeException: m | not_checkable peer_error: RuntimeException: m | fail call_failed: RuntimeException: m
        """.trimIndent()
    }
}
