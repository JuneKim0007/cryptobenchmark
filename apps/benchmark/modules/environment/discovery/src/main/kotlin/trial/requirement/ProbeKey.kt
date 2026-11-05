package io.github.junekim0007.cryptobench.discovery.trial.requirement

import io.github.junekim0007.cryptobench.discovery.trial.call.KeyBits
import java.security.Key
import java.security.KeyPair
import javax.crypto.SecretKey

internal class ProbeKey private constructor(
    val source: String,
    val algorithm: String,
    val provider: String,
    val secret: SecretKey?,
    val pair: KeyPair?,
) {

    val encrypting: Key get() = secret ?: pair!!.public

    val decrypting: Key get() = secret ?: pair!!.private

    val isRawSecret: Boolean get() = secret != null && source != FACTORY && secret.encoded != null

    val bits: Int? get() = KeyBits.of(encrypting)

    fun describe(): Map<String, Any> = linkedMapOf<String, Any>(
        "source" to source,
        "algorithm" to algorithm,
        "class" to encrypting.javaClass.name,
    ).apply {
        if (provider.isNotEmpty()) put("provider", provider)
        bits?.let { put("bits", it) }
    }

    companion object {

        const val GENERATOR = "KeyGenerator"
        const val PAIR_GENERATOR = "KeyPairGenerator"
        const val FACTORY = "SecretKeyFactory"
        const val RAW = "SecretKeySpec"

        fun secret(source: String, algorithm: String, provider: String, key: SecretKey) = ProbeKey(source, algorithm, provider, key, null)

        fun pair(algorithm: String, provider: String, keys: KeyPair) = ProbeKey(PAIR_GENERATOR, algorithm, provider, null, keys)
    }
}
