package io.github.junekim0007.cryptobench.discovery.trial.requirement

// Whether one instance's operation runs twice: setup, op = a, op = b, and a new instance's op = c. Untimed; never benchmark evidence.
internal object ResetRun {

    const val SETUP_REFUSED = "setup_refused"
    const val FIRST_CALL_REFUSED = "first_call_refused"
    private const val SAME = "same"
    private const val RANDOMIZED = "randomized"
    private const val NOT_COMPARED = "not_compared"
    private const val OUTPUT_DIFFERS = "output_differs"
    private const val NOT_REVERSED = "not_reversed"

    fun <E : Any> of(order: CallOrder<E>, reverses: ((E, ByteArray) -> Boolean)? = null): Map<String, Any> {
        val calls = order.described()
        val engine = runCatching(order.make).getOrElse { return cannotRun(calls, SETUP_REFUSED, it) }
        val first = runCatching { order.run(engine) }.getOrElse { return cannotRun(calls, FIRST_CALL_REFUSED, it) }
        val second = runCatching { order.run(engine) }.getOrElse { return refused(calls, it) }
        if (first.contentEquals(second)) return result(calls, true, SAME)
        val fresh = runCatching { order.run(order.make()) }.getOrElse { return cannotRun(calls, SETUP_REFUSED, it) }
        if (first.contentEquals(fresh)) return result(calls, false, OUTPUT_DIFFERS)
        val reversed = reverses == null || runCatching { reverses(engine, second) }.getOrDefault(false)
        return result(calls, reversed, if (reversed) RANDOMIZED else NOT_REVERSED)
    }

    /** A generator's output is random and nothing takes it back: the second call running is the whole test. */
    fun <E : Any> ofGenerator(order: CallOrder<E>): Map<String, Any> {
        val calls = order.described()
        val engine = runCatching(order.make).getOrElse { return cannotRun(calls, SETUP_REFUSED, it) }
        runCatching { order.run(engine) }.onFailure { return cannotRun(calls, FIRST_CALL_REFUSED, it) }
        return runCatching { order.run(engine) }.fold({ result(calls, true, NOT_COMPARED) }, { refused(calls, it) })
    }

    private fun result(calls: Map<String, Any>, resets: Boolean, output: String): Map<String, Any> =
        linkedMapOf("resets" to resets, "output" to output, "calls" to calls)

    private fun refused(calls: Map<String, Any>, thrown: Throwable): Map<String, Any> =
        linkedMapOf("resets" to false, "refusedBy" to thrown.javaClass.simpleName, "detail" to ErrorText.of(thrown), "calls" to calls)

    private fun cannotRun(calls: Map<String, Any>, code: String, thrown: Throwable): Map<String, Any> =
        linkedMapOf("cannotRun" to code, "detail" to ErrorText.of(thrown), "calls" to calls)
}
