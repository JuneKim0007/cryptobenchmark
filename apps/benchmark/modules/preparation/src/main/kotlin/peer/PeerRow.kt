package io.github.junekim0007.cryptobench.preparation.peer

/** One operation's peer check: what the produced call must hold, the consumer's engine set up from it, its call, and the verdict on what that returned. */
internal interface PeerRow {

    fun ready(produced: ProducedCall): Outcome?

    // what it returns is the consuming call; everything before it is setup
    fun setup(produced: ProducedCall, consumer: Consumer): () -> Any?

    fun judge(produced: ProducedCall, consumed: Any?): Outcome
}

internal fun agrees(same: Boolean, failure: String): Outcome = if (same) Outcome.Pass else Outcome.Fail(failure)
