package io.github.junekim0007.cryptobench.discovery.trial.requirement

/** One engine's real calls in order: `setup` once, by `make`; `operation` each time it is used. Written to the record as `plan.calls`; a later plan check runs the same form. */
internal class CallOrder<E : Any>(private val setup: List<String>, val make: () -> E, private val operation: List<CallStep<E>>) {

    fun run(engine: E): ByteArray =
        operation.fold(ByteArray(0)) { out, step -> step.call(engine)?.let { out + it } ?: out }

    fun described(): Map<String, Any> = linkedMapOf("setup" to ArrayList(setup), "operation" to operation.mapTo(ArrayList()) { it.name })
}

internal class CallStep<E : Any>(val name: String, val call: (E) -> ByteArray?)
