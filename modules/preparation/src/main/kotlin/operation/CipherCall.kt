package io.github.junekim0007.cryptobench.preparation.operation

import java.security.GeneralSecurityException
import javax.crypto.Cipher

/** One timed doFinal into a buffer allocated once; init repeats only when the parameters change per call or the provider refuses a repeat. */
internal class CipherCall(private val cipher: Cipher, private val input: ByteArray, private val init: (Int) -> Unit, perCallParameters: Boolean) {

    private val output: ByteArray
    val reinitialises: Boolean
    private var calls = 0
    private var written = 0

    init {
        init(0)
        output = ByteArray(cipher.getOutputSize(input.size))
        reinitialises = perCallParameters || !repeats()
    }

    private fun repeats(): Boolean {
        val repeated = try {
            cipher.doFinal(input, 0, input.size, output, 0)
            cipher.doFinal(input, 0, input.size, output, 0)
            true
        } catch (refused: GeneralSecurityException) {
            false
        } catch (refused: IllegalStateException) {
            false
        }
        try {
            init(0)
        } catch (refused: GeneralSecurityException) {
            throw IllegalArgumentException("not_repeatable: the provider refuses these parameters twice; draw them with fresh(n)", refused)
        }
        return repeated
    }

    fun invoke(): ByteArray {
        if (reinitialises) init(++calls)
        written = cipher.doFinal(input, 0, input.size, output, 0)
        return output
    }

    fun exact(@Suppress("UNUSED_PARAMETER") result: Any?): ByteArray = output.copyOf(written)

    fun invocation(): Invocation = Invocation(::invoke, ::exact)
}
