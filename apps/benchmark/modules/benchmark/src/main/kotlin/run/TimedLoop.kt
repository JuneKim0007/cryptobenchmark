package io.github.junekim0007.cryptobench.benchmark.run

import io.github.junekim0007.cryptobench.preparation.operation.Invocation

object TimedLoop {

    fun run(invocation: Invocation, nanos: Long, clock: () -> Long = System::nanoTime): Long {
        // afterCall stays inside the window: an energy window is one trace slice per case, so its energy is in the window either way.
        val timed = invocation.step { it() }
        var calls = 0L
        val start = clock()
        while (clock() - start < nanos) {
            BlackHole.consume(timed.once())
            calls++
        }
        return calls
    }
}
