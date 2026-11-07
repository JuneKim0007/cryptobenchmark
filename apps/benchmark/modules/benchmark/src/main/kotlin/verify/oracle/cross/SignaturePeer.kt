package io.github.junekim0007.cryptobench.benchmark.verify.oracle.cross

import io.github.junekim0007.cryptobench.benchmark.verify.OutputBytes
import io.github.junekim0007.cryptobench.benchmark.verify.oracle.CheckedCall
import io.github.junekim0007.cryptobench.preparation.input.OperationInput
import io.github.junekim0007.cryptobench.preparation.interop.report.Outcome
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import java.security.PublicKey
import java.security.Signature

/** Sign: the peer verifies the case's signature with its public key. Verify: the peer accepts the signature the case accepted. */
internal object SignaturePeer : PeerCheck {

    override fun against(call: CheckedCall, peer: String): Outcome {
        val prepared = call.prepared
        val pair = prepared.key.keyPairsOrNull?.first() ?: return Outcome.NotCheckable("no_key_pair")
        val (message, signature) = if (prepared.case.operation == Operation.SIGN) {
            val output = OutputBytes.of(call.output) ?: return Outcome.Fail("not_bytes: ${call.output?.javaClass?.simpleName}")
            ((prepared.input as? OperationInput.Message)?.bytes ?: ByteArray(prepared.case.inputSize ?: 0)) to output
        } else {
            val input = prepared.input as? OperationInput.SignedMessage ?: return Outcome.NotCheckable("no_signed_input")
            input.message to input.signature
        }
        val reported = runCatching { (call.invocation.engine as? Signature)?.parameters }.getOrNull()
        return PeerRun.of({
            val spec = PeerParameters.spec(PeerParameters.used(prepared, if (prepared.parameters == null) null else reported))
            Signature.getInstance(prepared.case.algorithm, peer).apply {
                spec?.let { setParameter(it) }
                initVerify(PeerKey.of(pair.public, peer) as PublicKey)
            }
        }) { verifier ->
            verifier.update(message)
            PeerRun.agrees(verifier.verify(signature), "peer_rejects: the peer does not verify the case's signature")
        }
    }
}
