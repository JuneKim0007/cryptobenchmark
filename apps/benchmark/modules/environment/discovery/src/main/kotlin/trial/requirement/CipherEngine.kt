package io.github.junekim0007.cryptobench.discovery.trial.requirement

import java.security.AlgorithmParameters
import java.security.Key
import java.security.Provider
import java.security.spec.AlgorithmParameterSpec
import javax.crypto.Cipher

// A new instance for each call, the same order as preparation's EngineCall per INSTANCE_INIT_AND_OPERATION: create, init, operate.
internal class CipherEngine(private val provider: Provider, private val name: String) {

    fun create(): Cipher = Cipher.getInstance(name, provider)

    fun encrypting(key: Key, spec: AlgorithmParameterSpec?): Cipher = initialised(Cipher.ENCRYPT_MODE, key, spec)

    fun initialised(mode: Int, key: Key, spec: AlgorithmParameterSpec?): Cipher = create().also { init(it, mode, key, spec) }

    fun encrypt(key: Key, spec: AlgorithmParameterSpec?, message: ByteArray, aad: ByteArray? = null): ByteArray =
        encrypting(key, spec).let { cipher ->
            aad?.let { cipher.updateAAD(it) }
            cipher.doFinal(message)
        }

    fun decrypting(key: Key, sent: Sent): Cipher = create().also { cipher ->
        when {
            sent.parameters != null -> cipher.init(Cipher.DECRYPT_MODE, key, sent.parameters)
            sent.spec != null -> cipher.init(Cipher.DECRYPT_MODE, key, sent.spec)
            else -> cipher.init(Cipher.DECRYPT_MODE, key)
        }
    }

    fun decrypt(key: Key, sent: Sent, data: ByteArray, aad: ByteArray? = null): ByteArray =
        decrypting(key, sent).let { cipher ->
            aad?.let { cipher.updateAAD(it) }
            cipher.doFinal(data)
        }

    /** What the decrypt side receives: the parameters the provider reports for this encryption, else the spec it was given. */
    class Sent(val spec: AlgorithmParameterSpec?, val parameters: AlgorithmParameters? = null)

    companion object {
        fun init(cipher: Cipher, mode: Int, key: Key, spec: AlgorithmParameterSpec?) {
            if (spec == null) cipher.init(mode, key) else cipher.init(mode, key, spec)
        }
    }
}
