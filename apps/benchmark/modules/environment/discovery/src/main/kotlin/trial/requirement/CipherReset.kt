package io.github.junekim0007.cryptobench.discovery.trial.requirement

import io.github.junekim0007.cryptobench.jca.failure.ErrorText
import java.security.spec.AlgorithmParameterSpec
import javax.crypto.Cipher

// The reset test of a cipher per direction, on the base CipherFacts found: updateAAD runs only where this cipher takes it.
internal class CipherReset(private val engine: CipherEngine, private val base: CipherBase) {

    fun measure(): Map<String, Any> {
        val fixed = ParameterSpecs.fresh(base.like)
        return if (base.wrapOnly) wrapping(fixed) else doFinal(fixed)
    }

    private fun doFinal(fixed: AlgorithmParameterSpec?): Map<String, Any> {
        val key = base.key
        val aad = ParameterSpecs.random(AAD_BYTES).takeIf { added -> ErrorText.refusal { engine.encrypting(key.encrypting, ParameterSpecs.fresh(base.like)).updateAAD(added) } == null }
        val forward = CallOrder(listOf(INIT), { engine.encrypting(key.encrypting, fixed) }, steps(aad, base.message))
        val back = { cipher: Cipher, output: ByteArray -> engine.decrypt(key.decrypting, CipherEngine.Sent(fixed, cipher.parameters), output, aad).contentEquals(base.message) }
        return linkedMapOf(FORWARD to ResetRun.of(forward, back), REVERSE to ResetRun.of(reverse(fixed, aad)))
    }

    private fun reverse(fixed: AlgorithmParameterSpec?, aad: ByteArray?): CallOrder<Cipher> {
        val sealed by lazy {
            engine.encrypting(base.key.encrypting, fixed).let { cipher ->
                aad?.let { cipher.updateAAD(it) }
                CipherEngine.Sent(fixed, cipher.parameters) to cipher.doFinal(base.message)
            }
        }
        return CallOrder(listOf(INIT), { engine.decrypting(base.key.decrypting, sealed.first) }, steps(aad) { sealed.second })
    }

    private fun steps(aad: ByteArray?, input: ByteArray): List<CallStep<Cipher>> = steps(aad) { input }

    private fun steps(aad: ByteArray?, input: () -> ByteArray): List<CallStep<Cipher>> = listOfNotNull(
        aad?.let { added -> CallStep<Cipher>("updateAAD") { cipher -> cipher.updateAAD(added); null } },
        CallStep("update") { cipher -> cipher.update(input()) },
        CallStep("doFinal") { cipher -> cipher.doFinal() },
    )

    private fun wrapping(fixed: AlgorithmParameterSpec?): Map<String, Any> {
        val key = base.key
        val secret = base.toWrap()
        val wrap = CallOrder(listOf(INIT), { engine.initialised(Cipher.WRAP_MODE, key.encrypting, fixed) }, listOf(CallStep("wrap") { cipher -> cipher.wrap(secret) }))
        val wrapped by lazy { engine.initialised(Cipher.WRAP_MODE, key.encrypting, fixed).wrap(secret) }
        val unwrap = CallOrder(listOf(INIT), { engine.initialised(Cipher.UNWRAP_MODE, key.decrypting, fixed) }, listOf(CallStep("unwrap") { cipher -> cipher.unwrap(wrapped, key.algorithm, Cipher.SECRET_KEY).encoded }))
        val back = { _: Cipher, output: ByteArray -> engine.initialised(Cipher.UNWRAP_MODE, key.decrypting, fixed).unwrap(output, key.algorithm, Cipher.SECRET_KEY).encoded.contentEquals(secret.encoded) }
        return linkedMapOf(FORWARD to ResetRun.of(wrap, back), REVERSE to ResetRun.of(unwrap))
    }

    private companion object {
        const val FORWARD = "forward"
        const val REVERSE = "reverse"
        const val INIT = "init"
        const val AAD_BYTES = 16
    }
}
