package io.github.junekim0007.cryptobench.discovery.trial.call

import io.github.junekim0007.cryptobench.discovery.contract.Attempt
import io.github.junekim0007.cryptobench.discovery.contract.KeyCacheStats
import io.github.junekim0007.cryptobench.discovery.contract.ServiceKey
import java.security.KeyPair
import java.security.KeyPairGenerator
import java.security.NoSuchAlgorithmException
import java.security.Provider
import java.security.interfaces.ECKey
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.SecretKeyFactory
import javax.crypto.interfaces.DHKey
import javax.crypto.spec.PBEKeySpec

// One cache per run, kept across trial levels: a refused generation is remembered too, since it refuses again.
internal class DefaultKeys(private val providers: List<Provider>) {

    class Secret(val algorithm: String, val provider: String, val key: SecretKey)

    class Pair(val algorithm: String, val provider: String, val keys: KeyPair)

    private val secrets = HashMap<String, Result<Secret>>()

    private val pairs = HashMap<String, Result<Pair>>()

    private val passwords = HashMap<String, Result<Secret>>()

    private var generated = 0

    private var refused = 0

    private var reused = 0

    private var generationNanos = 0L

    fun secret(preferred: Provider, algorithm: String, keySize: Int? = null): Secret =
        secretFrom(firstOffering(preferred, algorithm) { KeyGenerator.getInstance(algorithm, it) }, algorithm, keySize).getOrThrow()

    fun pair(preferred: Provider, algorithm: String): Pair =
        pairFrom(firstOffering(preferred, algorithm) { KeyPairGenerator.getInstance(algorithm, it) }, algorithm, null).getOrThrow()

    fun secretFrom(provider: Provider, algorithm: String, keySize: Int?): Result<Secret> =
        cached(secrets, cacheKey(provider, algorithm, keySize)) {
            val generator = KeyGenerator.getInstance(algorithm, provider)
            if (keySize != null) generator.init(keySize)
            Secret(algorithm, provider.name, generator.generateKey())
        }

    fun pairFrom(provider: Provider, algorithm: String, keySize: Int?): Result<Pair> =
        cached(pairs, cacheKey(provider, algorithm, keySize)) {
            val generator = KeyPairGenerator.getInstance(algorithm, provider)
            if (keySize != null) generator.initialize(keySize)
            Pair(algorithm, provider.name, generator.generateKeyPair())
        }

    // A factory for a password-based name may refuse a bare password and want a salted spec.
    fun passwordFrom(provider: Provider, algorithm: String): Result<Secret> =
        cached(passwords, cacheKey(provider, algorithm, null)) {
            val factory = SecretKeyFactory.getInstance(algorithm, provider)
            val key = Attempt.of { factory.generateSecret(PBEKeySpec(PASSWORD)) }
                .getOrElse { factory.generateSecret(PBEKeySpec(PASSWORD, ByteArray(SALT_BYTES) { it.toByte() }, ITERATIONS, DERIVED_BITS)) }
            Secret(algorithm, provider.name, key)
        }

    fun peer(own: Pair): KeyPair {
        val generator = KeyPairGenerator.getInstance(own.algorithm, own.provider)
        when (val public = own.keys.public) {
            is ECKey -> generator.initialize(public.params)
            is DHKey -> generator.initialize(public.params)
        }
        return generator.generateKeyPair()
    }

    fun stats(): KeyCacheStats = KeyCacheStats(generated, refused, reused, generationNanos / 1_000_000)

    private fun <T> cached(cache: HashMap<String, Result<T>>, key: String, make: () -> T): Result<T> {
        cache[key]?.let {
            reused++
            return it
        }
        val started = System.nanoTime()
        val made = Attempt.of(make)
        generationNanos += System.nanoTime() - started
        if (made.isSuccess) generated++ else refused++
        cache[key] = made
        return made
    }

    private fun firstOffering(preferred: Provider, algorithm: String, create: (Provider) -> Any): Provider {
        for (provider in listOf(preferred) + providers.filter { it.name != preferred.name }) {
            try {
                create(provider)
                return provider
            } catch (notOffered: NoSuchAlgorithmException) {
                continue
            }
        }
        throw NoSuchAlgorithmException("no provider generates $algorithm")
    }

    private fun cacheKey(provider: Provider, algorithm: String, keySize: Int?): String =
        provider.name + "|" + ServiceKey.fold(algorithm) + "|" + keySize

    private companion object {
        val PASSWORD = "requirement-probe".toCharArray()
        const val SALT_BYTES = 16
        const val ITERATIONS = 1000
        const val DERIVED_BITS = 256
    }
}
