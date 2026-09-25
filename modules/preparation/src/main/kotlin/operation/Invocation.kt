package io.github.junekim0007.cryptobench.preparation.operation

class Invocation(
    val perIteration: () -> Any?,
    val setUp: () -> Unit = {},
) {

    fun once(): Any? {
        setUp()
        return perIteration()
    }
}
