package io.github.junekim0007.cryptobench.discovery.trial.call

import io.github.junekim0007.cryptobench.discovery.contract.DefaultRunOutcome
import io.github.junekim0007.cryptobench.discovery.contract.TriedKey
import java.security.Key
import java.security.KeyPairGenerator
import java.security.Provider
import javax.crypto.KeyGenerator

internal class GeneratorCall(private val pair: Boolean) : DefaultCall {

    override val takesInput: Boolean = false

    override fun call(provider: Provider, algorithm: String, input: ByteArray, keys: DefaultKeys): DefaultRunOutcome {
        val (key, secret) = generate(provider, algorithm, null)
        val bits = KeyBits.of(key)
        return DefaultRunOutcome(works = true, keySize = bits, keyMaterial = materialOf(secret), keyFormat = secret.format.orEmpty(),
            triedKeys = sizesBeside(bits).map { tried(provider, algorithm, it) })
    }

    // a pair's parameters can take minutes to generate: no size above what the default run already paid for
    private fun sizesBeside(default: Int?): List<Int> =
        if (pair) PAIR_SIZES.filter { default != null && it < default } else SECRET_SIZES.filter { it != default }

    private fun tried(provider: Provider, algorithm: String, size: Int): TriedKey =
        try {
            val secret = generate(provider, algorithm, size).second
            TriedKey(size, materialOf(secret), secret.format.orEmpty())
        } catch (_: Exception) {
            TriedKey(size, refused = true)
        } catch (_: LinkageError) {
            TriedKey(size, refused = true)
        }

    /** The key to size, and the key whose encoding decides: a pair's private key, since its public key always encodes. */
    private fun generate(provider: Provider, algorithm: String, size: Int?): Pair<Key, Key> = generating(provider, algorithm, size)()

    /** One generator, made and sized once; each call of the result generates. */
    fun generating(provider: Provider, algorithm: String, size: Int?): () -> Pair<Key, Key> =
        if (pair) {
            val generator = KeyPairGenerator.getInstance(algorithm, provider)
            size?.let { generator.initialize(it) }
            ({ generator.generateKeyPair().let { it.public to it.private } })
        } else {
            val generator = KeyGenerator.getInstance(algorithm, provider)
            size?.let { generator.init(it) }
            ({ generator.generateKey().let { it to it } })
        }

    private fun materialOf(key: Key): String =
        if (key.encoded == null) DefaultRunOutcome.NON_EXPORTABLE else DefaultRunOutcome.EXPORTABLE

    private companion object {
        val SECRET_SIZES = listOf(128, 192, 256)
        val PAIR_SIZES = listOf(256, 384, 1024, 2048)
    }
}
