package io.github.junekim0007.cryptobench.benchmark.verify.observe

import io.github.junekim0007.cryptobench.preparation.key.plan.KeyRecipe
import io.github.junekim0007.cryptobench.preparation.operation.CallTrace
import io.github.junekim0007.cryptobench.preparation.operation.Invocation
import io.github.junekim0007.cryptobench.preparation.operation.PerCall
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import javax.crypto.Cipher

/** What one harness call actually did, read from the invocation's trace and engine before and after it; oracle/ judges it. */
class ObservedCall private constructor(private val prepared: PreparedCase, private val invocation: Invocation) {

    private val before: CallTrace? = invocation.trace
    private val ivBefore: ByteArray? = (invocation.engine as? Cipher)?.iv

    /** steps null: untraced. iv null: the engine reports none. */
    class Observation(val record: Map<String, Any>, val calls: Int, val steps: List<String>?, val initsPerCall: Int, val iv: Iv?)

    class Iv(val byProvider: Boolean, val distinct: Boolean)

    fun finish(calls: Int): Observation {
        val after = invocation.trace
        val record = linkedMapOf<String, Any>("calls" to calls)
        var steps: List<String>? = null
        var inits = 0
        if (before == null || after == null || calls == 0) {
            record["steps"] = "untraced"
        } else {
            val newInstance = after.engine !== before.engine
            inits = (after.inits - before.inits) / calls
            steps = listOfNotNull(GET_INSTANCE.takeIf { newInstance }, INIT.takeIf { inits > 0 }, OPERATION)
            record.putAll(linkedMapOf("steps" to steps, "newInstance" to newInstance, "initsPerCall" to inits))
        }
        val iv = (invocation.engine as? Cipher)?.iv?.let { ivAfter ->
            Iv(prepared.parameters == null, ivBefore == null || !ivBefore.contentEquals(ivAfter)).also {
                record["iv"] = linkedMapOf("by" to by(it), "bytes" to ivAfter.size, "distinctFromPreviousCall" to it.distinct)
            }
        }
        record["key"] = key()
        return Observation(record, calls, steps, inits, iv)
    }

    private fun key(): Map<String, Any> {
        val provider = when (val recipe = prepared.recipe) {
            is KeyRecipe.Secret -> recipe.provider
            is KeyRecipe.Pair -> recipe.provider
            else -> null
        }
        val key = prepared.key.secretKeyOrNull ?: prepared.key.keyPairsOrNull?.first()?.public
        return linkedMapOf<String, Any>("kind" to prepared.recipe.kind).apply {
            if (provider != null) {
                put("provider", provider)
                put("by", if (provider == prepared.case.provider) "same" else "foreign")
            }
            key?.let { put("class", it.javaClass.name) }
        }
    }

    companion object {
        const val GET_INSTANCE = "getInstance"
        const val INIT = "init"
        const val OPERATION = "operation"
        private const val PROVIDER = "provider"
        private const val HARNESS = "harness"

        fun start(prepared: PreparedCase, invocation: Invocation) = ObservedCall(prepared, invocation)

        fun by(iv: Iv): String = if (iv.byProvider) PROVIDER else HARNESS

        fun steps(perCall: PerCall): List<String> = when (perCall) {
            PerCall.OPERATION -> listOf(OPERATION)
            PerCall.INIT_AND_OPERATION -> listOf(INIT, OPERATION)
            PerCall.INSTANCE_INIT_AND_OPERATION -> listOf(GET_INSTANCE, INIT, OPERATION)
        }
    }
}
