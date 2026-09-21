package io.github.junekim0007.cryptobench.discovery.contract

data class TrialOutcome(
    val instantiates: Boolean,
    val error: String = "",
) {

    init {
        require(instantiates == error.isEmpty()) { "an outcome carries an error exactly when it fails" }
    }

    companion object {

        val SUCCESS = TrialOutcome(instantiates = true)

        fun failure(throwable: Throwable): TrialOutcome =
            TrialOutcome(instantiates = false, error = throwable.javaClass.simpleName + ": " + throwable.message.orEmpty())

        fun failure(reason: String): TrialOutcome = TrialOutcome(instantiates = false, error = reason)
    }
}
