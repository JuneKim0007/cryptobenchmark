package io.github.junekim0007.cryptobench.config.source

import io.github.junekim0007.cryptobench.contract.trial.DefaultRunOutcome
import io.github.junekim0007.cryptobench.contract.trial.TrialReport

data class TrialView(
    val entries: List<Entry>,
    val defaultRunInputSize: Int? = null,
    val keystore: List<KeystoreRow> = emptyList(),
) {

    data class Entry(
        val provider: String,
        val type: String,
        val name: String,
        val run: DefaultRun,
    )

    data class DefaultRun(
        val works: Boolean,
        val keyAlgorithm: String = "",
        val keyProvider: String = "",
        val keySize: Int? = null,
        val inputSize: Int? = null,
        val providerChose: String = "",
        val bareName: Boolean = false,
        val error: String = "",
    )

    companion object {

        fun of(trial: TrialReport): TrialView {
            val entries = trial.services.flatMap { service ->
                val own = service.defaultRun?.let { Entry(service.provider, service.type, service.algorithm, defaultRun(it)) }
                listOfNotNull(own) + service.transformations.mapNotNull { transformation ->
                    transformation.defaultRun?.let { Entry(service.provider, service.type, transformation.name, defaultRun(it)) }
                }
            }
            val keystore = requireNotNull(trial.keystore) { "missing_field: keystore" }
            return TrialView(entries, trial.defaultRunInputSize, keystore.rows.map {
                KeystoreRow(it.provider, it.type, it.algorithm, it.backing, it.keySize, it.curve, it.supported, it.error)
            })
        }

        private fun defaultRun(run: DefaultRunOutcome): DefaultRun =
            DefaultRun(run.works, run.keyAlgorithm, run.keyProvider, run.keySize, run.inputSize, run.providerChose, run.bareName, run.error)
    }
}
