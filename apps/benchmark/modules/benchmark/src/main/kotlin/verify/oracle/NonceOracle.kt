package io.github.junekim0007.cryptobench.benchmark.verify.oracle

import io.github.junekim0007.cryptobench.benchmark.verify.observe.ObservedCall
import io.github.junekim0007.cryptobench.preparation.interop.report.Outcome
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.parameter.resolve.ResolvedParameters
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase

/** Encrypt that re-inits with a drawn per-init IV must show a new IV each call; every other IV is recorded, not asserted. */
object NonceOracle {

    const val NAME = "nonce"

    fun judge(observation: ObservedCall.Observation, prepared: PreparedCase): Judgement {
        val iv = observation.iv ?: return Judgement(Outcome.NotCheckable("no_iv: the engine reports none"))
        val by = mapOf("by" to ObservedCall.by(iv))
        if (ResolvedParameters.IV_BYTES !in prepared.resolvedParameters) {
            return Judgement(Outcome.NotCheckable("constant_iv: preparation read this IV back as a constant, not a per-init value"), by)
        }
        val drawn = iv.byProvider || prepared.parameters?.varies == true
        if (prepared.case.operation != Operation.ENCRYPT || observation.initsPerCall <= 0 || !drawn) {
            return Judgement(Outcome.NotCheckable("not_asserted: an IV repeats by design unless encrypt re-inits with a drawn one"), by)
        }
        return Judgement(if (iv.distinct) Outcome.Pass else Outcome.Fail("iv_repeated: encrypt re-initialised with the same IV as the previous call"), by)
    }
}
