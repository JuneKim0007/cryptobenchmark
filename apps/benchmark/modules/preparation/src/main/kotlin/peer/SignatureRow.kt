package io.github.junekim0007.cryptobench.preparation.peer

import io.github.junekim0007.cryptobench.jca.failure.Attempt
import io.github.junekim0007.cryptobench.preparation.input.OperationInput
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.operation.CaseArguments
import java.security.PublicKey
import java.security.Signature

/** Sign: the consumer verifies the call's signature with its public key. Verify: the consumer accepts the signature the call accepted. */
internal object SignatureRow : PeerRow {

    override fun ready(produced: ProducedCall): Outcome? {
        if (signs(produced) && OutputBytes.of(produced.output) == null) return Outcome.Fail("not_bytes: ${produced.output?.javaClass?.simpleName}")
        if (produced.prepared.key.keyPairsOrNull == null) return Outcome.NotCheckable("no_key_pair")
        if (!signs(produced) && produced.prepared.input !is OperationInput.SignedMessage) return Outcome.NotCheckable("no_signed_input")
        return null
    }

    override fun setup(produced: ProducedCall, consumer: Consumer): () -> Any? {
        val prepared = produced.prepared
        val (message, signature) = if (signs(produced)) {
            CaseArguments.preparedMessage(prepared) to OutputBytes.of(produced.output)!!
        } else {
            (prepared.input as OperationInput.SignedMessage).let { it.message to it.signature }
        }
        // parameters only when the case binds them: an engine may report defaults another provider refuses
        val reported = if (prepared.parameters == null) null else Attempt.of { (produced.engine as? Signature)?.parameters }.getOrNull()
        val spec = PeerParameters.spec(PeerParameters.used(prepared, reported))
        val verifier = Signature.getInstance(consumer.algorithm, consumer.provider).apply {
            spec?.let { setParameter(it) }
            initVerify(PeerKey.of(prepared.key.keyPairsOrNull!!.first().public, consumer.provider) as PublicKey)
        }
        return { verifier.update(message); verifier.verify(signature) }
    }

    override fun judge(produced: ProducedCall, consumed: Any?): Outcome =
        agrees(consumed == true, "peer_rejects: the peer does not verify the case's signature")

    private fun signs(produced: ProducedCall) = produced.prepared.case.operation == Operation.SIGN
}
