package io.github.junekim0007.cryptobench.benchmark.verify.oracle.cross

import io.github.junekim0007.cryptobench.benchmark.verify.oracle.CheckedCall
import io.github.junekim0007.cryptobench.preparation.interop.report.Outcome
import java.security.KeyPair

/** A generated key pair: the peer's KeyFactory rebuilds both halves, the public one to the same encoding. A secret key has no peer recomputation. */
internal object KeyOutputPeer : PeerCheck {

    // A private key's PKCS#8 may legitimately carry optional fields one provider writes and another drops; only the public encoding is canonical.
    override fun against(call: CheckedCall, peer: String): Outcome {
        val pair = call.output as? KeyPair ?: return Outcome.NotCheckable("no_peer_check: a generated secret key has nothing a peer recomputes")
        return PeerRun.of({ PeerKey.of(pair.private, peer); PeerKey.of(pair.public, peer) }) { public ->
            PeerRun.agrees(public.encoded.contentEquals(pair.public.encoded), "peer_differs: the peer re-encodes the generated public key differently")
        }
    }
}
