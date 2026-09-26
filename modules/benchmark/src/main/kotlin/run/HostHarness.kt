package io.github.junekim0007.cryptobench.benchmark.run

import io.github.junekim0007.cryptobench.preparation.operation.Invocations
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase

class HostHarness(
    private val warmupNanos: Long = WARMUP_NANOS,
    private val runNanos: Long = RUN_NANOS,
    private val runs: Int = RUNS,
) {

    fun measure(prepared: PreparedCase): CaseMeasurement {
        val invocation = Invocations.of(prepared)
        var warmupIterations = 0L
        val warmupStart = System.nanoTime()
        while (System.nanoTime() - warmupStart < warmupNanos) {
            invocation.setUp()
            BlackHole.consume(invocation.perIteration())
            warmupIterations++
        }
        val observedNanos = (System.nanoTime() - warmupStart).toDouble() / warmupIterations
        val iterations = maxOf(1, (runNanos / maxOf(1.0, observedNanos)).toInt())
        val samples = prepared.case.harness.iterations ?: runs
        val nanosPerOperation = (1..samples).map {
            val start = System.nanoTime()
            repeat(iterations) {
                invocation.setUp()
                BlackHole.consume(invocation.perIteration())
            }
            (System.nanoTime() - start) / iterations
        }
        return CaseMeasurement(prepared.case, iterations, nanosPerOperation)
    }

    companion object {
        const val WARMUP_NANOS = 200_000_000L
        const val RUN_NANOS = 30_000_000L
        const val RUNS = 5
    }
}
