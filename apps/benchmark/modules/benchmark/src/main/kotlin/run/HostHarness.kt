package io.github.junekim0007.cryptobench.benchmark.run

import io.github.junekim0007.cryptobench.benchmark.budget.NativeBudget
import io.github.junekim0007.cryptobench.preparation.operation.Invocations
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import io.github.junekim0007.cryptobench.settings.Metric

class HostHarness(
    private val warmupNanos: Long = WARMUP_NANOS,
    private val runNanos: Long = RUN_NANOS,
    private val runs: Int = RUNS,
    private val cleanupEvery: Int = NativeBudget.CALLS,
) {

    fun measure(prepared: PreparedCase): CaseMeasurement {
        val invocation = Invocations.of(prepared)
        val budget = NativeBudget(cleanupEvery)
        val warmupStart = System.nanoTime()
        val warmupIterations = TimedLoop.run(invocation, warmupNanos, budget = budget)
        val observedNanos = (System.nanoTime() - warmupStart).toDouble() / maxOf(1L, warmupIterations)
        val iterations = maxOf(1, (runNanos / maxOf(1.0, observedNanos)).toInt())
        val samples = prepared.case.harness.iterations ?: runs
        val nanosPerOperation = (1..samples).map {
            var paused = 0L
            val start = System.nanoTime()
            repeat(iterations) {
                BlackHole.consume(invocation.perIteration())
                if (budget.due()) paused += budget.clean()
            }
            (System.nanoTime() - start - paused).toDouble() / iterations
        }
        return CaseMeasurement(prepared.case, prepared.recipe.kind, iterations, nanosPerOperation, prepared.resolvedParameters, budget.spent)
    }

    companion object {
        const val WARMUP_NANOS = 200_000_000L
        const val RUN_NANOS = 30_000_000L
        const val RUNS = 5
        val METRICS: Set<Metric> = setOf(Metric.TIME)

        // The check's call: no warm-up and no timer, the output to the hook instead of the BlackHole.
        val ONCE = OneCall { invocation, hook -> hook.consume(invocation.once()) }
    }
}
