package io.github.junekim0007.cryptobench.discovery.trial.requirement

import io.github.junekim0007.cryptobench.discovery.contract.Attempt
import io.github.junekim0007.cryptobench.discovery.contract.ErrorText

// One call per fact: a call that throws records its error under that fact, and the next fact still runs.
internal class FactSheet {

    val facts = linkedMapOf<String, Any>()

    fun measure(name: String, block: () -> Any?) {
        Attempt.of(block)
            .onSuccess { value -> if (value != null) facts[name] = value }
            .onFailure { facts[name] = mapOf(ERROR to ErrorText.of(it)) }
    }

    private companion object {
        const val ERROR = "error"
    }
}
