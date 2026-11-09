package io.github.junekim0007.cryptobench.benchmark.run

import io.github.junekim0007.cryptobench.preparation.operation.Invocations
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import io.github.junekim0007.cryptobench.settings.Metric

class HostHarness(
    private val warmupNanos: Long = WARMUP_NANOS,
    private val runNanos: Long = RUN_NANOS,
    private val runs: Int = RUNS,
    // The JVM's own count; passed in because this module also compiles for Android, which has no java.lang.management.
    private val collectionCount: () -> Long,
) {

    fun measure(prepared: PreparedCase): CaseMeasurement {
        val invocation = Invocations.of(prepared)
        val warmupStart = System.nanoTime()
        val warmupIterations = TimedLoop.run(invocation, warmupNanos)
        val observedNanos = (System.nanoTime() - warmupStart).toDouble() / maxOf(1L, warmupIterations)
        val iterations = maxOf(1, (runNanos / maxOf(1.0, observedNanos)).toInt())
        val samples = prepared.case.harness.iterations ?: runs
        val cleaning = SampleCleaning(collectionCount)
        val nanosPerOperation = (1..samples).map {
            cleaning.beforeSample()
            val start = System.nanoTime()
            repeat(iterations) { BlackHole.consume(invocation.perIteration()) }
            val elapsed = System.nanoTime() - start
            cleaning.afterSample()
            elapsed.toDouble() / iterations
        }
        return CaseMeasurement(prepared.case, prepared.recipe.kind, iterations, nanosPerOperation, prepared.resolvedParameters, cleaning.cleaned)
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
