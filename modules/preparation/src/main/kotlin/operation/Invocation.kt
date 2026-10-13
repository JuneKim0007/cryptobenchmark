package io.github.junekim0007.cryptobench.preparation.operation

/** perIteration is what the harness times; once() is one call's exact result, for checks outside the timed loop. */
class Invocation(val perIteration: () -> Any?, private val exact: (Any?) -> Any? = { it }) {

    fun once(): Any? = exact(perIteration())
}
