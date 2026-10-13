package io.github.junekim0007.cryptobench.benchmark.run.decorate

import io.github.junekim0007.cryptobench.benchmark.run.TimedLoop
import io.github.junekim0007.cryptobench.benchmark.run.compose.CaseRun
import io.github.junekim0007.cryptobench.preparation.operation.Invocation

class Rewarm(private val inner: CaseRun, private val invocation: Invocation, private val warmupNanos: Long) : CaseRun {

    override fun run(): Long? {
        TimedLoop.run(invocation, warmupNanos)
        return inner.run()
    }
}
