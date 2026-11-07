package io.github.junekim0007.cryptobench.preparation.operation

/** perIteration is what the harness times; once() is one call's exact result; again() repeats the last call with the parameters it drew; engine is the JCA object it last called, for read-back. */
class Invocation(
    val perIteration: () -> Any?,
    private val exact: (Any?) -> Any? = { it },
    private val engineOf: () -> Any? = { null },
    val perCall: PerCall = PerCall.OPERATION,
    private val traceOf: () -> CallTrace? = { null },
    private val replay: () -> Any? = perIteration,
) {

    val engine: Any? get() = engineOf()

    val trace: CallTrace? get() = traceOf()

    fun once(): Any? = exact(perIteration())

    fun again(): Any? = exact(replay())
}
