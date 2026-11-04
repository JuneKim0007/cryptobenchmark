package io.github.junekim0007.cryptobench.benchmark.run

object BlackHole {

    private var last: Any? = null

    fun consume(value: Any?) {
        last = value
    }
}
