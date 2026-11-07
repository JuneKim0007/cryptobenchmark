package io.github.junekim0007.cryptobench.discovery.trial.call

import io.github.junekim0007.cryptobench.discovery.contract.Attempt
import io.github.junekim0007.cryptobench.discovery.contract.DefaultRunOutcome
import io.github.junekim0007.cryptobench.discovery.contract.ParameterReadBack
import java.security.Key
import java.security.Provider
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.OAEPParameterSpec

internal object CipherCall : DefaultCall {

    override val takesInput: Boolean = true

    override fun call(provider: Provider, algorithm: String, input: ByteArray, keys: DefaultKeys): DefaultRunOutcome {
        val cipher = Cipher.getInstance(algorithm, provider)
        val key = encryptionKey(provider, algorithm, keys)
        cipher.init(Cipher.ENCRYPT_MODE, key.key)
        cipher.doFinal(input)
        return DefaultRunOutcome(
            works = true,
            keyAlgorithm = key.algorithm,
            keyProvider = key.provider,
            keySize = KeyBits.of(key.key),
            fixedKeySize = key.fixedSize,
            providerChose = chosenParameters(cipher, key.key),
            bareName = !algorithm.contains('/'),
        )
    }

    private class EncryptionKey(val algorithm: String, val provider: String, val key: Key, val fixedSize: Int? = null)

    private fun encryptionKey(provider: Provider, algorithm: String, keys: DefaultKeys): EncryptionKey {
        for ((name, size) in KeyNames.cipherCandidates(algorithm)) {
            val secret = Attempt.of { keys.secret(provider, name, size) }.getOrNull() ?: continue
            return EncryptionKey(secret.algorithm, secret.provider, secret.key, size)
        }
        val pair = keys.pair(provider, KeyNames.cipherBase(algorithm))
        return EncryptionKey(pair.algorithm, pair.provider, pair.keys.public)
    }

    // key=value pairs named as prepared.yaml resolvedParameters, read back as level 3 does; a value the provider fills in identically on every init is not an IV.
    fun chosenParameters(cipher: Cipher, key: Key): String {
        val spec = cipher.parameters?.let { ParameterReadBack.readable(it) }
        if (spec is GCMParameterSpec || spec is OAEPParameterSpec) {
            return ParameterReadBack.describe(spec).filterKeys { it != ParameterReadBack.CLASS }.entries.joinToString(" ") { "${it.key}=${it.value}" }
        }
        val chosen = cipher.iv ?: return ""
        cipher.init(Cipher.ENCRYPT_MODE, key)
        return if (chosen.contentEquals(cipher.iv)) "fixedValueBytes=${chosen.size}" else "ivBytes=${chosen.size}"
    }
}
