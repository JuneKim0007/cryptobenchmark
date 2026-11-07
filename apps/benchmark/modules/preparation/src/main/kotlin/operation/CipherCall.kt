package io.github.junekim0007.cryptobench.preparation.operation

import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import java.security.GeneralSecurityException
import javax.crypto.Cipher

/** One timed doFinal into a buffer allocated once; the setup catalog decides whether init and getInstance run inside it. */
internal class CipherCall(create: () -> Cipher, private val input: ByteArray, init: EngineInit<Cipher>) {

    private val call = EngineCall(create, init, ::operate)
    private val output = ByteArray(outputSize(call.engine))
    private var written = 0

    // a wrap cipher answers getOutputSize with -1: one doFinal before timing learns the size instead
    private fun outputSize(cipher: Cipher): Int = cipher.getOutputSize(input.size).takeIf { it >= 0 } ?: cipher.doFinal(input).size

    private fun operate(cipher: Cipher): ByteArray {
        written = cipher.doFinal(input, 0, input.size, output, 0)
        return output
    }

    fun invocation(case: BenchmarkCase, catalog: SetupCatalog = SetupCatalog.standard): Invocation =
        invocation(catalog.perCall(case) { call.engine.iv != null })

    fun invocation(perCall: PerCall): Invocation {
        val invocation = call.invocation(perCall, { output.copyOf(written) }, readBack = true)
        operate(call.engine)
        try {
            invocation.perIteration()
        } catch (refused: GeneralSecurityException) {
            throw notRepeatable(perCall, refused)
        } catch (refused: IllegalStateException) {
            throw notRepeatable(perCall, refused)
        }
        return invocation
    }

    private fun notRepeatable(perCall: PerCall, cause: Exception) = IllegalArgumentException(
        if (perCall == PerCall.OPERATION) "not_repeatable: the provider refuses a second doFinal without init, which the setup catalog keeps outside the call"
        else "not_repeatable: the provider refuses these parameters twice; draw them with fresh(n)",
        cause,
    )
}
