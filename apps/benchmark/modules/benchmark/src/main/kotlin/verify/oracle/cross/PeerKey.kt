package io.github.junekim0007.cryptobench.benchmark.verify.oracle.cross

import java.security.Key
import java.security.KeyFactory
import java.security.PrivateKey
import java.security.PublicKey
import java.security.Security
import java.security.spec.KeySpec
import java.security.spec.PKCS8EncodedKeySpec
import java.security.spec.X509EncodedKeySpec
import javax.crypto.SecretKey
import javax.crypto.spec.SecretKeySpec

/** The case's key in the peer's own representation: rebuilt by the peer's KeyFactory from its standard encoding, a secret from its raw bytes. */
internal object PeerKey {

    private const val REJECTED = "peer_key_rejected"

    fun of(key: Key, peer: String): Key = when (key) {
        is SecretKey -> SecretKeySpec(encoded(key), key.algorithm)
        is PublicKey -> rebuilt(key, peer, X509EncodedKeySpec(encoded(key))) { factory, spec -> factory.generatePublic(spec) }
        is PrivateKey -> rebuilt(key, peer, PKCS8EncodedKeySpec(encoded(key))) { factory, spec -> factory.generatePrivate(spec) }
        else -> throw PeerRefusal(REJECTED, "unknown_key: ${key.javaClass.simpleName}")
    }

    private fun encoded(key: Key): ByteArray = key.encoded ?: throw PeerRefusal(REJECTED, "no_encoding: the ${key.algorithm} key exports no bytes")

    // The key's own algorithm name first, then every KeyFactory the peer registers: the encoding's algorithm identifier decides which parses it.
    private fun rebuilt(key: Key, peer: String, spec: KeySpec, generate: (KeyFactory, KeySpec) -> Key): Key {
        val provider = Security.getProvider(peer) ?: throw PeerRefusal(REJECTED, "not_installed: $peer")
        val names = listOf(key.algorithm) + provider.services.filter { it.type == "KeyFactory" }.map { it.algorithm }.sorted()
        for (name in names.distinct()) {
            val rebuilt = runCatching { generate(KeyFactory.getInstance(name, provider), spec) }.getOrNull()
            if (rebuilt != null) return rebuilt
        }
        throw PeerRefusal(REJECTED, "no KeyFactory of $peer rebuilds the ${key.algorithm} ${key.format} encoding")
    }
}
