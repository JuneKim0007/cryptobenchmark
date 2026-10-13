package io.github.junekim0007.cryptobench.preparation.operation

class Invocation(val perIteration: () -> Any?) {

    fun once(): Any? = perIteration()
}
