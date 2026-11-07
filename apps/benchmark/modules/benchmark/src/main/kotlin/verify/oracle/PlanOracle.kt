package io.github.junekim0007.cryptobench.benchmark.verify.oracle

import io.github.junekim0007.cryptobench.benchmark.verify.observe.ObservedCall
import io.github.junekim0007.cryptobench.preparation.interop.report.Outcome
import io.github.junekim0007.cryptobench.preparation.operation.PerCall

/** The observed call against today's plan: exactly one harness call, and the steps it made are the ones perCall plans. */
object PlanOracle {

    const val NAME = "plan"

    fun judge(observation: ObservedCall.Observation, perCall: PerCall): Judgement {
        val steps = observation.steps
        val planned = ObservedCall.steps(perCall)
        return Judgement(when {
            observation.calls == 0 -> Outcome.NotCheckable("no_call: the harness made none")
            steps == null -> Outcome.NotCheckable("untraced: this invocation keeps no call trace")
            observation.calls != 1 -> Outcome.Fail("calls: the harness made ${observation.calls} calls, the check expects one")
            steps != planned -> Outcome.Fail("steps: observed $steps, ${perCall.label} plans $planned")
            else -> Outcome.Pass
        })
    }
}
