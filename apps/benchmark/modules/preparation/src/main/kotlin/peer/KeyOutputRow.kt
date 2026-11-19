package io.github.junekim0007.cryptobench.preparation.peer

import java.security.KeyPair

/** A generated key pair: the consumer's KeyFactory rebuilds both halves, the public one to the same encoding. A secret key has no peer recomputation. */
internal object KeyOutputRow : PeerRow {

    override fun ready(produced: ProducedCall): Outcome? =
        if (produced.output is KeyPair) null else Outcome.NotCheckable("no_peer_check: a generated secret key has nothing a peer recomputes")

    // A private key's PKCS#8 may legitimately carry optional fields one provider writes and another drops; only the public encoding is canonical.
    override fun setup(produced: ProducedCall, consumer: Consumer): () -> Any? {
        val pair = produced.output as KeyPair
        PeerKey.of(pair.private, consumer.provider)
        val public = PeerKey.of(pair.public, consumer.provider)
        return { public.encoded }
    }

    override fun judge(produced: ProducedCall, consumed: Any?): Outcome =
        agrees((consumed as? ByteArray).contentEquals((produced.output as KeyPair).public.encoded), "peer_differs: the peer re-encodes the generated public key differently")
}
