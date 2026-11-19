package io.github.junekim0007.cryptobench.preparation.peer

import io.github.junekim0007.cryptobench.jca.failure.Attempt
import io.github.junekim0007.cryptobench.preparation.measurement.Operation

/** One procedure for every peer check: the operation's row, what the call must hold, the consumer's setup and call, each failure through [Outcomes]. */
object PeerEngine {

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

    fun checks(operation: Operation): Boolean = operation in ROWS

    fun check(produced: ProducedCall, consumer: Consumer): Outcome {
        val operation = produced.prepared.case.operation
        val row = ROWS[operation] ?: return Outcome.NotCheckable("no_peer_check: $operation")
        row.ready(produced)?.let { return it }
        val consume = Attempt.of { row.setup(produced, consumer) }.getOrElse { return Outcomes.of(Stage.SETUP, it) }
        val consumed = Attempt.of { consume() }.getOrElse { return Outcomes.of(Stage.CONSUME, it) }
        return row.judge(produced, consumed)
    }
}
