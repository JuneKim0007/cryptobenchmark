package io.github.junekim0007.cryptobench.discovery.trial

import io.github.junekim0007.cryptobench.contract.trial.DefaultRunOutcome
import io.github.junekim0007.cryptobench.contract.trial.TrialOutcome
import io.github.junekim0007.cryptobench.jca.failure.ErrorText

internal fun TrialOutcome.Companion.of(attempted: Result<*>): TrialOutcome = attempted.fold({ SUCCESS }, { failure(it) })

internal fun TrialOutcome.Companion.failure(throwable: Throwable): TrialOutcome =
    TrialOutcome(instantiates = false, error = ErrorText.of(throwable))

internal fun DefaultRunOutcome.Companion.failure(throwable: Throwable): DefaultRunOutcome =
    DefaultRunOutcome(works = false, error = ErrorText.of(throwable))
