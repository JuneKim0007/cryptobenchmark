package io.github.junekim0007.cryptobench.preparation.device.dto

import io.github.junekim0007.cryptobench.contract.trial.TrialReport

data class TrialledDevice(
    val services: List<TrialledService>,
) {

    companion object {
        fun of(trial: TrialReport): TrialledDevice = TrialledDevice(
            trial.services.map { service ->
                TrialledService(
                    provider = service.provider,
                    type = service.type,
                    algorithm = service.algorithm,
                    instantiates = service.outcome.instantiates,
                    error = service.outcome.error,
                    keyAlgorithm = service.defaultRun?.keyAlgorithm.orEmpty(),
                    fixedKeySize = service.defaultRun?.fixedKeySize,
                    transformations = service.transformations.map {
                        TrialledTransformation(it.name, it.outcome.instantiates, it.outcome.error, it.defaultRun?.keyAlgorithm.orEmpty(), it.defaultRun?.fixedKeySize)
                    },
                )
            },
        )
    }
}
