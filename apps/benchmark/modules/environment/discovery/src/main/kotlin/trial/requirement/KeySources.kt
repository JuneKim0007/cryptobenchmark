package io.github.junekim0007.cryptobench.discovery.trial.requirement

import io.github.junekim0007.cryptobench.jca.failure.Attempt
import io.github.junekim0007.cryptobench.discovery.contract.CapturedEnvironment
import io.github.junekim0007.cryptobench.discovery.contract.ServiceKey
import io.github.junekim0007.cryptobench.discovery.trial.call.DefaultKeys
import io.github.junekim0007.cryptobench.discovery.trial.call.KeyNames
import java.security.KeyPair
import java.security.Provider
import java.security.SecureRandom
import java.security.interfaces.ECKey
import java.security.interfaces.RSAKey
import javax.crypto.spec.SecretKeySpec

// Keys a service may run on, likeliest first; the service's own call decides, so a wrong guess costs one refused init.
internal class KeySources(capture: CapturedEnvironment, private val providers: List<Provider>, private val keys: DefaultKeys) {

    private val generatorNames: List<String> = capture.providers.flatMap { it.services }
        .filter { ServiceKey.fold(it.type) in GENERATOR_TYPES }
        .map { it.algorithm }
        .distinctBy { ServiceKey.fold(it) }
        .sortedByDescending { it.length }

    fun of(type: String, algorithm: String, preferred: Provider, pairsOnly: Boolean = false): Sequence<ProbeKey> = sequence {
        val order = listOf(preferred) + providers.filter { it.name != preferred.name }
        for ((name, size) in names(type, algorithm)) {
            for (provider in order) {
                if (!pairsOnly) keys.secretFrom(provider, name, size).getOrNull()?.let { yield(ProbeKey.secret(ProbeKey.GENERATOR, it.algorithm, it.provider, it.key)) }
                keys.pairFrom(provider, name, null).getOrNull()?.let { yield(ProbeKey.pair(it.algorithm, it.provider, it.keys)) }
                if (!pairsOnly) password(provider, name).getOrNull()?.let { yield(it) }
            }
        }
        if (!pairsOnly) {
            val base = algorithm.substringBefore('/')
            for (length in RAW_LENGTHS) yield(ProbeKey.secret(ProbeKey.RAW, base, "", SecretKeySpec(random(length), base)))
        }
    }

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

    private fun names(type: String, algorithm: String): List<Pair<String, Int?>> {
        val ruled = KeyNames.candidates(type, algorithm)
        val known = ruled.mapTo(HashSet()) { ServiceKey.fold(it.first) }
        val folded = ServiceKey.fold(algorithm)
        return ruled + generatorNames.filter { ServiceKey.fold(it) !in known && ServiceKey.fold(it) in folded }.map { it to null }
    }

    private companion object {
        val GENERATOR_TYPES = setOf("KEYGENERATOR", "KEYPAIRGENERATOR", "SECRETKEYFACTORY")
        val RAW_LENGTHS = listOf(16, 32, 24, 8)
        val RANDOM = SecureRandom()
        fun random(length: Int) = ByteArray(length).also { RANDOM.nextBytes(it) }
    }
}
