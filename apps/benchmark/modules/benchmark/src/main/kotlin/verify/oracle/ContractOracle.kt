package io.github.junekim0007.cryptobench.benchmark.verify.oracle

import io.github.junekim0007.cryptobench.benchmark.verify.oracle.contract.AgreeProperties
import io.github.junekim0007.cryptobench.benchmark.verify.oracle.contract.DecryptProperties
import io.github.junekim0007.cryptobench.benchmark.verify.oracle.contract.DigestProperties
import io.github.junekim0007.cryptobench.benchmark.verify.oracle.contract.EncryptProperties
import io.github.junekim0007.cryptobench.benchmark.verify.oracle.contract.KeyOutputProperties
import io.github.junekim0007.cryptobench.benchmark.verify.oracle.contract.Properties
import io.github.junekim0007.cryptobench.benchmark.verify.oracle.contract.SignProperties
import io.github.junekim0007.cryptobench.benchmark.verify.oracle.contract.VerifyProperties
import io.github.junekim0007.cryptobench.preparation.interop.report.Outcome
import io.github.junekim0007.cryptobench.preparation.measurement.Operation

/** The operation's contract properties over the call's own output; any failed property fails it, all unprovable leaves it not_checkable. */
class ContractOracle : Oracle {

    override val name = "contract"

    override fun judge(call: CheckedCall): Judgement {
        val properties = PROPERTIES[call.prepared.case.operation]
            ?: return Judgement(Outcome.NotCheckable("no_contract: ${call.prepared.case.operation}"))
        val verdicts = properties.of(call)
        val failed = verdicts.filterValues { it is Outcome.Fail }
        val outcome = when {
            failed.isNotEmpty() -> Outcome.Fail(failed.entries.joinToString("; ") { (name, verdict) -> "$name: ${(verdict as Outcome.Fail).reason}" })
            verdicts.values.any { it == Outcome.Pass } -> Outcome.Pass
            else -> Outcome.NotCheckable(verdicts.values.joinToString("; ") { (it as Outcome.NotCheckable).reason })
        }
        return Judgement(outcome, mapOf("properties" to verdicts.mapValuesTo(LinkedHashMap()) { (_, verdict) -> verdict.label }))
    }

    private companion object {
        val PROPERTIES: Map<Operation, Properties> = mapOf(
            Operation.ENCRYPT to EncryptProperties,
            Operation.DECRYPT to DecryptProperties,
            Operation.SIGN to SignProperties,
            Operation.VERIFY to VerifyProperties,
            Operation.DIGEST to DigestProperties.DIGEST,
            Operation.COMPUTE_MAC to DigestProperties.MAC,
            Operation.GENERATE_KEY to KeyOutputProperties(pair = false),
            Operation.GENERATE_KEY_PAIR to KeyOutputProperties(pair = true),
            Operation.AGREE_KEY to AgreeProperties,
        )
    }
}
