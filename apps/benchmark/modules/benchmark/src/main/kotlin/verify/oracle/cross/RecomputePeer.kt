package io.github.junekim0007.cryptobench.benchmark.verify.oracle.cross

import io.github.junekim0007.cryptobench.benchmark.verify.OutputBytes
import io.github.junekim0007.cryptobench.benchmark.verify.oracle.CheckedCall
import io.github.junekim0007.cryptobench.preparation.input.OperationInput
import io.github.junekim0007.cryptobench.preparation.interop.report.Outcome
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import java.security.MessageDigest
import java.security.PrivateKey
import java.security.PublicKey
import javax.crypto.KeyAgreement
import javax.crypto.Mac

/** Deterministic operations: the peer recomputes digest, MAC or agreed secret from the case's key, parameters and input; the bytes must match. */
internal object RecomputePeer : PeerCheck {

    override fun against(call: CheckedCall, peer: String): Outcome {
        val prepared = call.prepared
        val output = OutputBytes.of(call.output) ?: return Outcome.Fail("not_bytes: ${call.output?.javaClass?.simpleName}")
        val message = (prepared.input as? OperationInput.Message)?.bytes ?: ByteArray(prepared.case.inputSize ?: 0)
        val algorithm = prepared.case.algorithm
        val recompute: () -> () -> ByteArray = when (prepared.case.operation) {
            Operation.DIGEST -> { { MessageDigest.getInstance(algorithm, peer).let { { it.digest(message) } } } }
            Operation.COMPUTE_MAC -> { {
                val key = PeerKey.of(prepared.key.secretKeyOrNull ?: throw PeerRefusal("no_key", "mac_needs_a_secret_key"), peer)
                val spec = PeerParameters.spec(PeerParameters.used(prepared, null))
                Mac.getInstance(algorithm, peer).apply { if (spec == null) init(key) else init(key, spec) }.let { { it.doFinal(message) } }
            } }
            Operation.AGREE_KEY -> { {
                val pairs = prepared.key.keyPairsOrNull ?: throw PeerRefusal("no_key", "agreement_needs_key_pairs")
                val private = PeerKey.of(pairs.first().private, peer) as PrivateKey
                val public = PeerKey.of(pairs.last().public, peer) as PublicKey
                val spec = PeerParameters.spec(PeerParameters.used(prepared, null))
                KeyAgreement.getInstance(algorithm, peer).apply { if (spec == null) init(private) else init(private, spec) }
                    .let { { it.doPhase(public, true); it.generateSecret() } }
            } }
            else -> return Outcome.NotCheckable("no_peer_check: ${prepared.case.operation}")
        }
        return PeerRun.of(recompute) { run -> PeerRun.agrees(run().contentEquals(output), "peer_differs: the peer computes other bytes from the same key, parameters and input") }
    }
}
