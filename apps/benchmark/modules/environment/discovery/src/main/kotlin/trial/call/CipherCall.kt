package io.github.junekim0007.cryptobench.discovery.trial.call

import io.github.junekim0007.cryptobench.discovery.contract.DefaultRunOutcome
import java.security.AlgorithmParameters
import java.security.Key
import java.security.Provider
import java.security.spec.AlgorithmParameterSpec
import java.security.spec.InvalidParameterSpecException
import java.security.spec.MGF1ParameterSpec
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.OAEPParameterSpec
import javax.crypto.spec.PSource

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
            val secret = runCatching { keys.secret(provider, name, size) }.getOrNull() ?: continue
            return EncryptionKey(secret.algorithm, secret.provider, secret.key, size)
        }
        val pair = keys.pair(provider, KeyNames.cipherBase(algorithm))
        return EncryptionKey(pair.algorithm, pair.provider, pair.keys.public)
    }

    // key=value pairs named as prepared.yaml resolvedParameters; a value the provider fills in identically on every init is not an IV.
    fun chosenParameters(cipher: Cipher, key: Key): String {
        val parameters = cipher.parameters
        val gcm = parameters?.let { spec(it, GCMParameterSpec::class.java) }
        if (gcm != null) return "ivBytes=${gcm.iv.size} tagBits=${gcm.tLen}"
        val oaep = parameters?.let { spec(it, OAEPParameterSpec::class.java) }
        if (oaep != null) {
            val fields = mutableListOf("digest=${oaep.digestAlgorithm}")
            (oaep.mgfParameters as? MGF1ParameterSpec)?.let { fields += "mgf1=${it.digestAlgorithm}" }
            (oaep.pSource as? PSource.PSpecified)?.let { fields += "labelBytes=${it.value.size}" }
            return fields.joinToString(" ")
        }
        val chosen = cipher.iv ?: return ""
        cipher.init(Cipher.ENCRYPT_MODE, key)
        return if (chosen.contentEquals(cipher.iv)) "fixedValueBytes=${chosen.size}" else "ivBytes=${chosen.size}"
    }

    private fun <T : AlgorithmParameterSpec> spec(parameters: AlgorithmParameters, type: Class<T>): T? = try {
        parameters.getParameterSpec(type)
    } catch (notThisType: InvalidParameterSpecException) {
        null
    }
}
