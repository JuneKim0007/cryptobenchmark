package io.github.junekim0007.cryptobench.preparation.operation

import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import java.security.GeneralSecurityException
import javax.crypto.Cipher

/** One timed doFinal into a buffer allocated once; the setup catalog decides whether init and getInstance run inside it. */
internal class CipherCall(create: () -> Cipher, private val input: ByteArray, init: (Cipher, Int) -> Unit) {

    private val call = EngineCall(create, init, ::operate)
    private val output = ByteArray(call.engine.getOutputSize(input.size))
    private var written = 0

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
