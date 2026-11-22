package io.github.junekim0007.cryptobench.discovery.trial.requirement

import io.github.junekim0007.cryptobench.jca.failure.Attempt
import io.github.junekim0007.cryptobench.discovery.trial.call.DefaultKeys
import io.github.junekim0007.cryptobench.discovery.trial.call.KeyGenerationSpec
import java.security.KeyPair
import java.security.Provider
import java.security.SecureRandom
import java.security.interfaces.ECKey
import java.security.interfaces.RSAKey
import javax.crypto.spec.SecretKeySpec

// Keys a service may run on, likeliest first; the service's own call decides, so a wrong guess costs one refused init.
internal class KeySources(private val providers: List<Provider>, private val keys: DefaultKeys) {

    fun of(type: String, algorithm: String, preferred: Provider, pairsOnly: Boolean = false): Sequence<ProbeKey> = sequence {
        val candidates = keys.candidates.of(type, algorithm, preferred.name)
        for (provider in keys.order(preferred)) {
            for (candidate in candidates) {
                val secrets = !pairsOnly && candidate.spec == null
                if (secrets) keys.secretFrom(provider, candidate.name, candidate.size).getOrNull()?.let { yield(ProbeKey.secret(ProbeKey.GENERATOR, it.algorithm, it.provider, it.key)) }
                keys.pairFrom(provider, candidate.name, null, candidate.spec).getOrNull()?.let { yield(ProbeKey.pair(it.algorithm, it.provider, it.keys)) }
                if (secrets) password(provider, candidate.name).getOrNull()?.let { yield(it) }
            }
        }
        if (!pairsOnly) {
            val base = keys.candidates.raw(type, algorithm, preferred.name)
            for (length in RAW_LENGTHS) yield(ProbeKey.secret(ProbeKey.RAW, base, "", SecretKeySpec(random(length), base)))
        }
    }

    // the entry's key-generation row that could not be made, as a tried key with its coded reason
    fun refusals(type: String, algorithm: String, preferred: Provider): List<Map<String, Any>> =
        (keys.candidates.keyGeneration(type, algorithm, preferred.name) as? KeyGenerationSpec.Refused)
            ?.let { listOf(mapOf("source" to KEY_GENERATION, "recipe" to it.recipe, "refused" to it.reason)) }.orEmpty()

    // The same algorithm and size from another provider; a size is asked for only when it costs no parameter generation.
    fun foreign(key: ProbeKey, provider: Provider): Result<ProbeKey> = Attempt.of {
        val secret = key.secret
        when {
            secret != null && key.source == ProbeKey.FACTORY ->
                password(provider, key.algorithm).getOrThrow()
            secret != null ->
                keys.secretFrom(provider, key.algorithm, key.bits).getOrThrow().let { ProbeKey.secret(ProbeKey.GENERATOR, it.algorithm, it.provider, it.key) }
            else -> {
                val default = keys.pairFrom(provider, key.algorithm, null).getOrThrow().let { ProbeKey.pair(it.algorithm, it.provider, it.keys) }
                if (default.bits == key.bits || !sizable(default)) default else sized(key, key.bits!!, provider).getOrThrow()
            }
        }
    }

    fun sized(key: ProbeKey, bits: Int, generatingProvider: Provider): Result<ProbeKey> =
        keys.pairFrom(generatingProvider, key.algorithm, bits).map { ProbeKey.pair(it.algorithm, it.provider, it.keys) }

    fun password(provider: Provider, name: String): Result<ProbeKey> =
        keys.passwordFrom(provider, name).map { ProbeKey.secret(ProbeKey.FACTORY, it.algorithm, it.provider, it.key) }

    fun generatorOf(key: ProbeKey): Provider? = providers.firstOrNull { it.name == key.provider }

    fun peer(key: ProbeKey): KeyPair = keys.peer(DefaultKeys.Pair(key.algorithm, key.provider, key.pair!!))

    fun sizable(key: ProbeKey): Boolean = key.pair?.public.let { it is RSAKey || it is ECKey }

    private companion object {
        val RAW_LENGTHS = listOf(16, 32, 24, 8)
        const val KEY_GENERATION = "keyGeneration"
        val RANDOM = SecureRandom()
        fun random(length: Int) = ByteArray(length).also { RANDOM.nextBytes(it) }
    }
}
