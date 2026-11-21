package io.github.junekim0007.cryptobench.preparation.peer

import io.github.junekim0007.cryptobench.document.catalogue.FamilyCatalogue
import io.github.junekim0007.cryptobench.jca.failure.Attempt
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyRecipe
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.port.DeviceCapability

/** One procedure for every peer check: the operation's row, what the call must hold, a generated key's use, the consumer's setup and call, each failure through [Outcomes]. */
class PeerEngine(capability: DeviceCapability) {

    private val uses = KeyUse(capability)

    // the producer's own call first: a pair's member that cannot make its output is producer_failed
    fun produced(case: BenchmarkCase, recipe: KeyRecipe, key: KeyMaterial, consumer: Consumer, travel: Travel): Outcome =
        check(Attempt.of { ProducedCall.of(case, recipe, key) }.getOrElse { return Outcomes.of(Stage.PRODUCE, it) }, consumer, travel)

    fun check(produced: ProducedCall, consumer: Consumer, travel: Travel): Outcome {
        val operation = produced.prepared.case.operation
        val row = ROWS[operation] ?: return Outcome.NotCheckable("no_peer_check: $operation")
        row.ready(produced)?.let { return it }
        return when (row) {
            is ConsumingRow -> consumed(row, produced, consumer, travel, Stage.SETUP)
            KeyOutputRow -> used(produced, consumer, travel)
        }
    }

    private fun used(produced: ProducedCall, consumer: Consumer, travel: Travel): Outcome {
        val case = produced.prepared.case
        val found = uses.of(case.type, case.algorithm, KeyOutputRow.algorithm(produced.output), case.provider, consumer.provider)
        val use = found.use ?: return Outcome.NotCheckable("no_key_use: no ${FamilyCatalogue.KEYED.joinToString()} entry of key.type ${found.keyTypes.joinToString(" or ")} " +
            "is Available on both ${case.provider} and ${consumer.provider} with a timed operation")
        return judgedBy(use, produced, consumer, travel).let {
            when (it) {
                is Outcome.Pass -> Outcome.Pass("use $use")
                is Outcome.Fail -> Outcome.Fail("${it.reason} (use $use)")
                is Outcome.NotCheckable -> Outcome.NotCheckable("${it.reason} (use $use)")
            }
        }
    }

    private fun judgedBy(use: KeyUse.Use, produced: ProducedCall, consumer: Consumer, travel: Travel): Outcome {
        val call = Attempt.of { KeyOutputRow.used(produced, use) }.getOrElse { return Outcomes.of(Stage.PRODUCE, it) }
        val row = ROWS.getValue(use.operation) as ConsumingRow
        row.ready(call)?.let { return it }
        return consumed(row, call, Consumer(consumer.provider, use.algorithm), travel, Stage.OUTPUT_KEY_SETUP)
    }

    private fun consumed(row: ConsumingRow, produced: ProducedCall, consumer: Consumer, travel: Travel, setup: Stage): Outcome {
        val consume = Attempt.of { row.setup(produced, consumer, travel) }.getOrElse { return Outcomes.of(setup, it) }
        return Attempt.of { row.judge(produced, consume()) }.getOrElse { Outcomes.of(Stage.CONSUME, it) }
    }

    companion object {

        private val ROWS: Map<Operation, PeerRow> = mapOf(
            Operation.ENCRYPT to CipherRow,
            Operation.DECRYPT to CipherRow,
            Operation.SIGN to SignatureRow,
            Operation.VERIFY to SignatureRow,
            Operation.DIGEST to RecomputeRow,
            Operation.COMPUTE_MAC to RecomputeRow,
            Operation.AGREE_KEY to RecomputeRow,
            Operation.GENERATE_KEY to KeyOutputRow,
            Operation.GENERATE_KEY_PAIR to KeyOutputRow,
        )

        const val PRODUCE_CONSUME = "produce_consume"
        const val SAME_OUTPUT = "same_output"
        const val NONE = "none"

        fun checks(operation: Operation): Boolean = operation in ROWS

        fun modeOf(operation: Operation): String = ROWS[operation]?.mode ?: NONE
    }
}
