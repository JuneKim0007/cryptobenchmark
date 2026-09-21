package io.github.junekim0007.cryptobench.discovery.contract

data class TransformationTrialEntry(
    val name: String,
    val outcome: TrialOutcome,
) {

    override fun toString(): String = "$name ${if (outcome.instantiates) "ok" else outcome.error}"
}
