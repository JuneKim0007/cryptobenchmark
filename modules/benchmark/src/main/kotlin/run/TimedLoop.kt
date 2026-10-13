package io.github.junekim0007.cryptobench.benchmark.run

import io.github.junekim0007.cryptobench.preparation.operation.Invocation

object TimedLoop {

    fun run(invocation: Invocation, nanos: Long, clock: () -> Long = System::nanoTime): Long {
        var calls = 0L
        val start = clock()
        while (clock() - start < nanos) {
            BlackHole.consume(invocation.once())
            calls++
        }
        return calls
    }
}
