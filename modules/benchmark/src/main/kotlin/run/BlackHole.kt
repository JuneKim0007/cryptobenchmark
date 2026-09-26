package io.github.junekim0007.cryptobench.benchmark.run

object BlackHole {

    @JvmStatic
    var last: Any? = null

    fun consume(value: Any?) {
        last = value
    }
}
