package io.github.junekim0007.cryptobench.preparation.key.plan

import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.operation.KeyShape
import io.github.junekim0007.cryptobench.preparation.operation.OperationDefinitions
import io.github.junekim0007.cryptobench.preparation.port.Availability
import io.github.junekim0007.cryptobench.preparation.port.DeviceCapability

class KeyPlanner(
    private val capability: DeviceCapability,
) {

    fun plan(case: BenchmarkCase): KeyRecipe {
        val shape = OperationDefinitions.of(case.operation).keyShape
        if (shape == KeyShape.NONE) {
            return KeyRecipe.None
        }
        val key = capability.measuredKey(case.provider, case.type, case.algorithm)
            ?: return KeyRecipe.Unavailable("no_measured_key: ${case.type}.${case.algorithm}")
        return when (shape) {
            KeyShape.NONE -> KeyRecipe.None
            KeyShape.SECRET -> secret(case, key) ?: unavailable(SECRET_GENERATOR, key.algorithm)
            KeyShape.PAIR -> pair(case, key, count = 1) ?: unavailable(PAIR_GENERATOR, key.algorithm)
            KeyShape.PEER_PAIRS -> pair(case, key, count = 2) ?: unavailable(PAIR_GENERATOR, key.algorithm)
            KeyShape.DEVICE_DECIDES -> secret(case, key) ?: pair(case, key, count = 1)
                ?: KeyRecipe.Unavailable("no_key_generator: ${key.algorithm}")
        }
    }

    private fun secret(case: BenchmarkCase, candidate: KeyCandidate): KeyRecipe.Secret? =
        generatingProvider(case, SECRET_GENERATOR, candidate.algorithm)
            ?.let { KeyRecipe.Secret(candidate.algorithm, case.keySize ?: candidate.keySize, it, case.keyParameters) }

    private fun pair(case: BenchmarkCase, candidate: KeyCandidate, count: Int): KeyRecipe.Pair? =
        generatingProvider(case, PAIR_GENERATOR, candidate.algorithm)
            ?.let { KeyRecipe.Pair(candidate.algorithm, case.keySize ?: candidate.keySize, it, count, case.keyParameters) }

    private fun generatingProvider(case: BenchmarkCase, generatorType: String, algorithm: String): String? =
        (listOf(case.provider) + capability.providers()).distinct()
            .firstOrNull { capability.check(it, generatorType, algorithm) == Availability.Available }

    private fun unavailable(generatorType: String, algorithm: String): KeyRecipe.Unavailable =
        KeyRecipe.Unavailable("no_key_generator: $generatorType.$algorithm")

    private companion object {
        const val SECRET_GENERATOR = "KeyGenerator"
        const val PAIR_GENERATOR = "KeyPairGenerator"
    }
}
