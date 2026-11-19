package io.github.junekim0007.cryptobench.preparation.peer

import io.github.junekim0007.cryptobench.jca.failure.Attempt
import java.security.Key
import java.security.KeyFactory
import java.security.PrivateKey
import java.security.Provider
import java.security.PublicKey
import java.security.Security
import java.security.spec.KeySpec
import java.security.spec.PKCS8EncodedKeySpec
import java.security.spec.X509EncodedKeySpec
import javax.crypto.SecretKey
import javax.crypto.spec.SecretKeySpec

/** The call's key in the consumer's representation: rebuilt from its standard encoding by the consumer's KeyFactory, else by the first installed provider's that rebuilds it; a secret from its raw bytes. */
internal object PeerKey {

    fun of(key: Key, consumer: String): Key = when (key) {
        is SecretKey -> SecretKeySpec(encoded(key), key.algorithm)
        is PublicKey -> rebuilt(key, consumer, X509EncodedKeySpec(encoded(key))) { factory, spec -> factory.generatePublic(spec) }
        is PrivateKey -> rebuilt(key, consumer, PKCS8EncodedKeySpec(encoded(key))) { factory, spec -> factory.generatePrivate(spec) }
        else -> throw PeerRefusal("peer_key_rejected", "unknown_key: ${key.javaClass.simpleName}")
    }

    private fun encoded(key: Key): ByteArray = key.encoded ?: throw PeerRefusal("key_not_extractable", "the ${key.algorithm} key exports no bytes")

    // A factory under the key's own name decides: its refusal is the consumer's. Otherwise the encoding's algorithm identifier decides which factory parses it.
    private fun rebuilt(key: Key, consumer: String, spec: KeySpec, generate: (KeyFactory, KeySpec) -> Key): Key {
        val own = Security.getProvider(consumer)
        if (own?.getService(FACTORY, key.algorithm) != null) return generate(KeyFactory.getInstance(key.algorithm, own), spec)
        val others = own?.let { factories(it) }.orEmpty().map { own!! to it } +
            Security.getProviders().filter { it.name != consumer && it.getService(FACTORY, key.algorithm) != null }.map { it to key.algorithm }
        for ((provider, name) in others) {
            Attempt.of { generate(KeyFactory.getInstance(name, provider), spec) }.getOrNull()?.let { return it }
        }
        throw PeerRefusal("peer_unavailable", "no KeyFactory of $consumer or another installed provider rebuilds the ${key.algorithm} ${key.format} encoding")
    }

    private fun factories(provider: Provider): List<String> = provider.services.filter { it.type == FACTORY }.map { it.algorithm }.sorted()

    private const val FACTORY = "KeyFactory"
}
