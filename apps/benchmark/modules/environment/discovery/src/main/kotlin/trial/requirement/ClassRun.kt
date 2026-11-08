package io.github.junekim0007.cryptobench.discovery.trial.requirement

import io.github.junekim0007.cryptobench.jca.failure.Attempt
import java.security.Provider

// The class a name really instantiates: a provider alias can land on a class its name does not suggest.
internal object ClassRun {

    fun of(provider: Provider, type: String, name: String): String =
        Attempt.of { provider.getService(type, name)?.newInstance(null)?.javaClass?.name }.getOrNull().orEmpty()
}
