package io.github.junekim0007.cryptobench.preparation.input

import java.security.AlgorithmParameters
import java.security.Key
import java.security.spec.AlgorithmParameterSpec
import javax.crypto.Cipher

sealed class OperationInput {

    object None : OperationInput()

    class Message(val bytes: ByteArray) : OperationInput()

    class Ciphertext(
        val bytes: ByteArray,
        val plaintextSize: Int,
        val spec: AlgorithmParameterSpec?,
        val providerParameters: AlgorithmParameters?,
    ) : OperationInput() {

        fun initDecrypting(cipher: Cipher, key: Key) {
            when {
                spec != null -> cipher.init(Cipher.DECRYPT_MODE, key, spec)
                providerParameters != null -> cipher.init(Cipher.DECRYPT_MODE, key, providerParameters)
                else -> cipher.init(Cipher.DECRYPT_MODE, key)
            }
        }
    }

    class SignedMessage(val message: ByteArray, val signature: ByteArray) : OperationInput()
}
