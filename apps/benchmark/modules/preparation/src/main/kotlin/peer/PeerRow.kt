package io.github.junekim0007.cryptobench.preparation.peer

/** One operation's peer check; ready says what the produced call must hold. */
internal sealed interface PeerRow {
    fun ready(produced: ProducedCall): Outcome?
}

/** A row whose consumer takes the call's own output: its engine set up from the call, its call, and the verdict on what that returned. */
internal interface ConsumingRow : PeerRow {

    // what it returns is the consuming call; everything before it is setup
    fun setup(produced: ProducedCall, consumer: Consumer): () -> Any?

    fun judge(produced: ProducedCall, consumed: Any?): Outcome
}

internal fun agrees(same: Boolean, failure: String): Outcome = if (same) Outcome.Pass else Outcome.Fail(failure)
