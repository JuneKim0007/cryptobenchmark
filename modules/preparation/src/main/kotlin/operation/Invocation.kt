package io.github.junekim0007.cryptobench.preparation.operation

/** perIteration is what the harness times; once() is one call's exact result; engine is the JCA object it calls, for read-back. */
class Invocation(val perIteration: () -> Any?, private val exact: (Any?) -> Any? = { it }, val engine: Any? = null) {

    fun once(): Any? = exact(perIteration())
}
