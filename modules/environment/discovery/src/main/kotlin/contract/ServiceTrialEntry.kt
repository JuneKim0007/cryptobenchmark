package io.github.junekim0007.cryptobench.discovery.contract

data class ServiceTrialEntry(
    val provider: String,
    val type: String,
    val algorithm: String,
    val outcome: TrialOutcome,
    val transformations: List<TransformationTrialEntry> = emptyList(),
    val defaultRun: DefaultRunOutcome? = null,
) {

    override fun toString(): String = "$provider $type.$algorithm ${if (outcome.instantiates) "ok" else outcome.error}"
}
