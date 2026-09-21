package io.github.junekim0007.cryptobench.discovery.trial

import io.github.junekim0007.cryptobench.discovery.contract.TrialOutcome

internal object Attempt {

    fun of(block: () -> Unit): TrialOutcome =
        try {
            block()
            TrialOutcome.SUCCESS
        } catch (exception: Exception) {
            TrialOutcome.failure(exception)
        } catch (linkageError: LinkageError) {
            TrialOutcome.failure(linkageError)
        }
}
