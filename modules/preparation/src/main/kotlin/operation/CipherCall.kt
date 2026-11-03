package io.github.junekim0007.cryptobench.preparation.operation

import java.security.GeneralSecurityException
import javax.crypto.Cipher

/** One timed init + doFinal into a buffer allocated once, the same for every cipher and mode. */
internal class CipherCall(private val cipher: Cipher, private val input: ByteArray, private val init: (Int) -> Unit) {

    private val output: ByteArray
    private var calls = 0
    private var written = 0

    init {
        init(calls++)
        output = ByteArray(cipher.getOutputSize(input.size))
        cipher.doFinal(input, 0, input.size, output, 0)
        try {
            invoke()
        } catch (refused: GeneralSecurityException) {
            throw notRepeatable(refused)
        } catch (refused: IllegalStateException) {
            throw notRepeatable(refused)
        }
    }

    private fun invoke(): ByteArray {
        init(calls++)
        written = cipher.doFinal(input, 0, input.size, output, 0)
        return output
    }

    private fun notRepeatable(cause: Exception) =
        IllegalArgumentException("not_repeatable: the provider refuses these parameters twice; draw them with fresh(n)", cause)

    fun invocation(): Invocation = Invocation(::invoke, { output.copyOf(written) }, cipher)
}
