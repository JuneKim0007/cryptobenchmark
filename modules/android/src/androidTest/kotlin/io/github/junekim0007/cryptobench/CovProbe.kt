package io.github.junekim0007.cryptobench

import androidx.benchmark.BlackHole
import androidx.test.platform.app.InstrumentationRegistry
import io.github.junekim0007.cryptobench.benchmark.run.TimedLoop
import io.github.junekim0007.cryptobench.preparation.operation.Invocations
import org.junit.Test
import java.io.File

// TEMP: CoV experiment, fixed ops per run without Jetpack; delete this file when the harness is redesigned.
class CovProbe {

    @Test
    fun runs() {
        val arguments = InstrumentationRegistry.getArguments()
        val sizes = (arguments.getString("ops") ?: "1000000").split(",").map { it.trim().toLong() }
        val runs = arguments.getString("runs")?.toInt() ?: 20
        val warmupNanos = ((arguments.getString("warmupSeconds")?.toDouble() ?: 2.0) * 1e9).toLong()
        val out = StringBuilder("runs: $runs\nwarmupNanos: $warmupNanos\ncases:\n")
        for (prepared in DevicePlan.timedCases) {
            val invocation = Invocations.of(prepared)
            TimedLoop.run(invocation, warmupNanos)
            out.append("- id: ${prepared.case.id}\n  inputBytes: ${prepared.case.inputSize ?: 0}\n  sizes:\n")
            for (ops in sizes) {
                val nanosPerOp = (1..runs).map {
                    val start = System.nanoTime()
                    var done = 0L
                    while (done < ops) {
                        BlackHole.consume(invocation.perIteration() ?: Unit)
                        done++
                    }
                    (System.nanoTime() - start).toDouble() / ops
                }
                out.append("  - ops: $ops\n    nsPerOp: [${nanosPerOp.joinToString()}]\n")
            }
        }
        File(DevicePlan.directory, FILE).writeText(out.toString())
    }

    companion object {
        const val FILE = "cov-probe.yaml"
    }
}
