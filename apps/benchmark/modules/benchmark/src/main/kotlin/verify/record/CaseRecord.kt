package io.github.junekim0007.cryptobench.benchmark.verify.record

import io.github.junekim0007.cryptobench.benchmark.check.RunnablePlan
import io.github.junekim0007.cryptobench.benchmark.verify.observe.ObservedCall
import io.github.junekim0007.cryptobench.benchmark.verify.oracle.Judgement
import io.github.junekim0007.cryptobench.preparation.peer.Outcome
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import io.github.junekim0007.cryptobench.settings.Skip
import io.github.junekim0007.cryptobench.preparation.shared.FailureText

/** One case of check.yaml: its plan, what ran, the outcome, every oracle's verdict, and the output digest where the call is deterministic. */
class CaseRecord(
    val id: String,
    val outcome: String,
    val fields: Map<String, Any>,
) {

    fun toMap(): Map<String, Any> = linkedMapOf<String, Any>("id" to id, "outcome" to outcome).apply { putAll(fields) }

    companion object {
        const val PASS = "pass"
        const val FAIL = "fail"
        const val ERROR = "error"
        const val NOT_RUN = "notRun"

        fun of(prepared: PreparedCase, observed: Map<String, Any>, judgements: Map<String, Judgement>, error: String?, digest: String?): CaseRecord {
            val outcome = when {
                error != null -> ERROR
                judgements.values.any { it.outcome is Outcome.Fail } -> FAIL
                else -> PASS
            }
            val fields = linkedMapOf<String, Any>(
                "case" to case(prepared),
                "plan" to linkedMapOf("perCall" to (prepared.perCall?.label ?: "none"), "steps" to stepsOf(prepared)),
                "observed" to observed,
                "oracles" to judgements.mapValuesTo(LinkedHashMap()) { (_, judgement) -> verdict(judgement) },
            )
            error?.let { fields["reason"] = FailureText.stable(it) }
            digest?.let { fields["outputDigest"] = it }
            return CaseRecord(prepared.case.id, outcome, fields)
        }

        // Skips sharing an id are numbered in the order of their fields, not of the skip list, so a rerun names each the same.
        fun fromSkips(skips: List<Skip>): List<CaseRecord> {
            val records = skips.map(::fromSkip)
            val numbered = records.groupBy { it.id }.values.filter { it.size > 1 }.flatMap { same ->
                same.sortedBy { it.fields.toString() }.mapIndexed { n, record -> record to "${record.id}#${n + 1}" }
            }.toMap()
            return records.map { record -> numbered[record]?.let { CaseRecord(it, record.outcome, record.fields) } ?: record }
        }

        // A case that ran and broke during the check is an error; a case stopped before it never ran.
        private fun fromSkip(skip: Skip): CaseRecord {
            // a rejection before expansion names no case: its service and code stand in
            val reason = FailureText.stable(skip.reason)
            val id = skip.caseId ?: listOfNotNull(skip.stage, skip.provider, skip.type, skip.name, skip.code).joinToString("|")
            return CaseRecord(id, if (skip.stage == RunnablePlan.CHECK) ERROR else NOT_RUN, linkedMapOf<String, Any>("stage" to skip.stage, "reason" to reason).apply {
                skip.provider?.let { put("provider", it) }
                skip.type?.let { put("type", it) }
                skip.name?.let { put("algorithm", it) }
            })
        }

        private fun case(prepared: PreparedCase): Map<String, Any> = linkedMapOf<String, Any>(
            "type" to prepared.case.type, "algorithm" to prepared.case.algorithm, "provider" to prepared.case.provider,
            "operation" to prepared.case.operation.name, "variant" to prepared.case.variant.label,
        ).apply {
            prepared.case.keySize?.let { put("keySize", it) }
            prepared.case.inputSize?.let { put("inputSize", it) }
        }

        private fun stepsOf(prepared: PreparedCase): Any =
            prepared.perCall?.let { ObservedCall.steps(it) } ?: "none"

        private fun verdict(judgement: Judgement): Map<String, Any> = linkedMapOf<String, Any>("verdict" to judgement.outcome.label).apply {
            when (val outcome = judgement.outcome) {
                is Outcome.Fail -> put("reason", FailureText.stable(outcome.reason))
                is Outcome.NotCheckable -> put("reason", FailureText.stable(outcome.reason))
                Outcome.Pass -> Unit
            }
            putAll(judgement.details)
        }
    }
}
