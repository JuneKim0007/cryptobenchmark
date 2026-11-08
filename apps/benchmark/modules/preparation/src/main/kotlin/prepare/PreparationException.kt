package io.github.junekim0007.cryptobench.preparation.prepare

/** A step of one case's preparation failed: the step's code and the provider's failure as one line. Any other Error is never wrapped. */
class PreparationException(val reason: String, cause: Throwable? = null) : IllegalStateException(reason, cause)
