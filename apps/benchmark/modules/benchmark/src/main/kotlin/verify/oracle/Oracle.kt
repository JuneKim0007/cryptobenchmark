package io.github.junekim0007.cryptobench.benchmark.verify.oracle

import io.github.junekim0007.cryptobench.preparation.interop.report.Outcome
import io.github.junekim0007.cryptobench.preparation.operation.Invocation
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase

/** One case's checked call: the case as prepared, the invocation that ran and what the call returned. */
class CheckedCall(val prepared: PreparedCase, val invocation: Invocation, val output: Any?)

/** A verdict with what supports it; not_checkable always carries a coded reason. */
class Judgement(val outcome: Outcome, val details: Map<String, Any> = emptyMap())

/** A check of one call's output, strongest first: known answers, cross-provider agreement, contract properties. */
interface Oracle {

    val name: String

    fun judge(call: CheckedCall): Judgement
}
