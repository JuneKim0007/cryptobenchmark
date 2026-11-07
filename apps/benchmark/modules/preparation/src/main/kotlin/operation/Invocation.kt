package io.github.junekim0007.cryptobench.preparation.operation

/** perIteration is what the harness times; once() is one call's exact result; engine is the JCA object it last called, for read-back. */
class Invocation(
    val perIteration: () -> Any?,
    private val exact: (Any?) -> Any? = { it },
    private val engineOf: () -> Any? = { null },
    val perCall: PerCall = PerCall.OPERATION,
    private val traceOf: () -> CallTrace? = { null },
) {

    val engine: Any? get() = engineOf()

    val trace: CallTrace? get() = traceOf()

    fun once(): Any? = exact(perIteration())
}
