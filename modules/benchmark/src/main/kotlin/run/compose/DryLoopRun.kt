package io.github.junekim0007.cryptobench.benchmark.run.compose

import io.github.junekim0007.cryptobench.benchmark.run.TimedLoop
import io.github.junekim0007.cryptobench.preparation.operation.Invocation

class DryLoopRun(private val invocation: Invocation, private val windowNanos: Long) : CaseRun {

    override fun run(): Long = TimedLoop.run(invocation, windowNanos)
}
