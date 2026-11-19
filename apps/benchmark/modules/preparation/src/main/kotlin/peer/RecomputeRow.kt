package io.github.junekim0007.cryptobench.preparation.peer

import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.operation.CaseArguments
import java.security.MessageDigest
import java.security.PrivateKey
import java.security.PublicKey
import javax.crypto.KeyAgreement
import javax.crypto.Mac

/** Deterministic operations: the consumer recomputes the digest, MAC or agreed secret (first pair's private, last pair's public) from the call's key, parameters and input. */
internal object RecomputeRow : ConsumingRow {

    override fun ready(produced: ProducedCall): Outcome? {
        if (OutputBytes.of(produced.output) == null) return Outcome.Fail("not_bytes: ${produced.output?.javaClass?.simpleName}")
        val key = produced.prepared.key
        return when (produced.prepared.case.operation) {
            Operation.COMPUTE_MAC -> if (key.secretKeyOrNull == null) Outcome.NotCheckable("no_key: mac_needs_a_secret_key") else null
            Operation.AGREE_KEY -> if (key.keyPairsOrNull == null) Outcome.NotCheckable("no_key: agreement_needs_key_pairs") else null
            else -> null
        }
    }

    override fun setup(produced: ProducedCall, consumer: Consumer): () -> Any? {
        val prepared = produced.prepared
        val message = CaseArguments.preparedMessage(prepared)
        val (provider, algorithm) = consumer
        when (prepared.case.operation) {
            Operation.COMPUTE_MAC -> {
                val mac = Mac.getInstance(algorithm, provider)
                val key = PeerKey.of(prepared.key.secretKeyOrNull!!, provider)
                val spec = PeerParameters.spec(PeerParameters.used(prepared, null))
                mac.apply { if (spec == null) init(key) else init(key, spec) }
                return { mac.doFinal(message) }
            }
            Operation.AGREE_KEY -> {
                val agreement = KeyAgreement.getInstance(algorithm, provider)
                val pairs = prepared.key.keyPairsOrNull!!
                val private = PeerKey.of(pairs.first().private, provider) as PrivateKey
                val public = PeerKey.of(pairs.last().public, provider) as PublicKey
                val spec = PeerParameters.spec(PeerParameters.used(prepared, null))
                agreement.apply { if (spec == null) init(private) else init(private, spec) }
                return { agreement.doPhase(public, true); agreement.generateSecret() }
            }
            else -> {
                val digest = MessageDigest.getInstance(algorithm, provider)
                return { digest.digest(message) }
            }
        }
    }

    override fun judge(produced: ProducedCall, consumed: Any?): Outcome =
        agrees((consumed as ByteArray).contentEquals(OutputBytes.of(produced.output)), "peer_differs: the peer computes other bytes from the same key, parameters and input")
}
