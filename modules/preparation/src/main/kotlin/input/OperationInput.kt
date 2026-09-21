package io.github.junekim0007.cryptobench.preparation.input

import java.security.AlgorithmParameters
import java.security.spec.AlgorithmParameterSpec

sealed class OperationInput {

    object None : OperationInput()

    class Message(val bytes: ByteArray) : OperationInput()

    class Ciphertext(
        val bytes: ByteArray,
        val plaintextSize: Int,
        val spec: AlgorithmParameterSpec?,
        val providerParameters: AlgorithmParameters?,
    ) : OperationInput()

    class SignedMessage(val message: ByteArray, val signature: ByteArray) : OperationInput()
}
