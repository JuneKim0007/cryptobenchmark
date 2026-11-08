package io.github.junekim0007.cryptobench.benchmark.run

import io.github.junekim0007.cryptobench.benchmark.budget.NativeBudget
import io.github.junekim0007.cryptobench.preparation.operation.Invocation

object TimedLoop {

    // With a budget its paused cleanups do not count toward the window.
    fun run(invocation: Invocation, nanos: Long, clock: () -> Long = System::nanoTime, budget: NativeBudget? = null): Long {
        var calls = 0L
        var paused = 0L
        val start = clock()
        while (clock() - start - paused < nanos) {
            BlackHole.consume(invocation.once())
            calls++
            if (budget != null && budget.due()) paused += budget.clean()
        }
        return calls
    }
}
