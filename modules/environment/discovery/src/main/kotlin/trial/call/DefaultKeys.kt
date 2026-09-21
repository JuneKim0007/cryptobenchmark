package io.github.junekim0007.cryptobench.discovery.trial.call

import io.github.junekim0007.cryptobench.discovery.contract.ServiceKey
import java.security.KeyPair
import java.security.KeyPairGenerator
import java.security.NoSuchAlgorithmException
import java.security.Provider
import java.security.interfaces.ECKey
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.interfaces.DHKey

/** Default keys for one trial run, generated once per (preferred provider, algorithm, size) and reused. */
internal class DefaultKeys(private val providers: List<Provider>) {

    class Secret(val algorithm: String, val provider: String, val key: SecretKey)

    class Pair(val algorithm: String, val provider: String, val keys: KeyPair)

    private val secrets = HashMap<String, Secret>()

    private val pairs = HashMap<String, Pair>()

    /** The preferred provider's generator when it has one, else the first in precedence order that does. */
    fun secret(preferred: Provider, algorithm: String, keySize: Int? = null): Secret =
        secrets.getOrPut(cacheKey(preferred, algorithm, keySize)) {
            val (provider, generator) = firstGenerator(preferred, algorithm) { KeyGenerator.getInstance(algorithm, it) }
            if (keySize != null) generator.init(keySize)
            Secret(algorithm, provider.name, generator.generateKey())
        }

    fun pair(preferred: Provider, algorithm: String): Pair =
        pairs.getOrPut(cacheKey(preferred, algorithm, null)) {
            val (provider, generator) = firstGenerator(preferred, algorithm) { KeyPairGenerator.getInstance(algorithm, it) }
            Pair(algorithm, provider.name, generator.generateKeyPair())
        }

    /** A second pair on the same domain parameters, as a key agreement's peer needs. */
    fun peer(own: Pair): KeyPair {
        val generator = KeyPairGenerator.getInstance(own.algorithm, own.provider)
        when (val public = own.keys.public) {
            is ECKey -> generator.initialize(public.params)
            is DHKey -> generator.initialize(public.params)
        }
        return generator.generateKeyPair()
    }

    private fun <G> firstGenerator(preferred: Provider, algorithm: String, create: (Provider) -> G): kotlin.Pair<Provider, G> {
        for (provider in listOf(preferred) + providers.filter { it.name != preferred.name }) {
            try {
                return provider to create(provider)
            } catch (notOffered: NoSuchAlgorithmException) {
                continue
            }
        }
        throw NoSuchAlgorithmException("no provider generates $algorithm")
    }

    private fun cacheKey(preferred: Provider, algorithm: String, keySize: Int?): String =
        preferred.name + "|" + ServiceKey.fold(algorithm) + "|" + keySize
}
