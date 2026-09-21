package io.github.junekim0007.cryptobench.discovery.trial.call

import io.github.junekim0007.cryptobench.discovery.contract.DefaultRunOutcome
import java.security.Key
import java.security.Provider
import java.security.spec.MGF1ParameterSpec
import javax.crypto.Cipher
import javax.crypto.spec.OAEPParameterSpec

/** Encrypts once with no parameters given, so whatever the provider fills in is recorded, not assumed. */
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
            providerChose = chosenParameters(cipher),
            bareName = !algorithm.contains('/'),
        )
    }

    private class EncryptionKey(val algorithm: String, val provider: String, val key: Key)

    /** A secret key when any provider generates one under the name, else the public half of a pair. */
    private fun encryptionKey(provider: Provider, algorithm: String, keys: DefaultKeys): EncryptionKey {
        for ((name, size) in KeyNames.cipherCandidates(algorithm)) {
            val secret = runCatching { keys.secret(provider, name, size) }.getOrNull() ?: continue
            return EncryptionKey(secret.algorithm, secret.provider, secret.key)
        }
        val pair = keys.pair(provider, KeyNames.cipherBase(algorithm))
        return EncryptionKey(pair.algorithm, pair.provider, pair.keys.public)
    }

    private fun chosenParameters(cipher: Cipher): String {
        val parameters = cipher.parameters ?: return ""
        val oaep = runCatching { parameters.getParameterSpec(OAEPParameterSpec::class.java) }.getOrNull()
        if (oaep != null) {
            val mgf = (oaep.mgfParameters as? MGF1ParameterSpec)?.digestAlgorithm ?: oaep.mgfAlgorithm
            return "OAEP digest=${oaep.digestAlgorithm} mgf1=$mgf"
        }
        return "${parameters.algorithm} iv=${cipher.iv?.size ?: 0}B"
    }
}
