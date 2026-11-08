package io.github.junekim0007.cryptobench.discovery.trial.requirement

import io.github.junekim0007.cryptobench.jca.failure.ErrorText

// A key of the same algorithm and size from every other provider: only a run tells which keys travel.
internal object ForeignKeys {

    private const val OK = "ok"

    fun of(service: ProbedService, key: ProbeKey, attempt: (ProbeKey) -> Unit): Map<String, Any> {
        val out = linkedMapOf<String, Any>()
        for (provider in service.providers) {
            if (provider.name == key.provider) continue
            val other = service.keys.foreign(key, provider).getOrNull() ?: continue
            out[provider.name] = ErrorText.refusal { attempt(other) } ?: OK
        }
        return out
    }
}
