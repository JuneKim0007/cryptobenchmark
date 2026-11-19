package io.github.junekim0007.cryptobench.jca

import io.github.junekim0007.cryptobench.jca.peer.PeerPair
import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Test
import java.security.KeyPair
import java.security.KeyPairGenerator
import java.security.interfaces.ECKey
import java.security.interfaces.XECKey
import java.security.spec.ECGenParameterSpec
import java.security.spec.NamedParameterSpec
import javax.crypto.KeyAgreement
import javax.crypto.interfaces.DHKey

class PeerPairTest {

    private fun pair(algorithm: String, init: KeyPairGenerator.() -> Unit) = KeyPairGenerator.getInstance(algorithm).apply(init).generateKeyPair()

    private fun peerOf(own: KeyPair, algorithm: String) = PeerPair.of(own, KeyPairGenerator.getInstance(algorithm))

    private fun agrees(own: KeyPair, peer: KeyPair, algorithm: String) {
        fun secret(private: KeyPair, public: KeyPair) = KeyAgreement.getInstance(algorithm).run { init(private.private); doPhase(public.public, true); generateSecret() }
        assertArrayEquals(secret(own, peer), secret(peer, own))
    }

    @Test
    fun aDhPeerSharesTheGroupOfAPairSizedByKeySize() {
        val own = pair("DH") { initialize(2048) }
        val peer = peerOf(own, "DH")
        assertEquals((own.public as DHKey).params.p, (peer.public as DHKey).params.p)
        assertEquals((own.public as DHKey).params.g, (peer.public as DHKey).params.g)
        agrees(own, peer, "DH")
    }

    @Test
    fun anEcPeerSharesTheCurve() {
        val own = pair("EC") { initialize(ECGenParameterSpec("secp384r1")) }
        val peer = peerOf(own, "EC")
        assertEquals((own.public as ECKey).params.order, (peer.public as ECKey).params.order)
        agrees(own, peer, "ECDH")
    }

    /** XDH's default is X25519: an X448 key's peer still gets X448, an X25519 key's peer the default unasked. */
    @Test
    fun anXecPeerSharesTheNamedCurve() {
        for (curve in listOf("X25519", "X448")) {
            val own = pair("XDH") { initialize(NamedParameterSpec(curve)) }
            val peer = peerOf(own, "XDH")
            assertEquals(curve, ((peer.public as XECKey).params as NamedParameterSpec).name)
            agrees(own, peer, "XDH")
        }
    }
}
