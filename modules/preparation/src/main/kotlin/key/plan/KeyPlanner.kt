package io.github.junekim0007.cryptobench.preparation.key.plan

import io.github.junekim0007.cryptobench.preparation.engine.EngineTypes
import io.github.junekim0007.cryptobench.preparation.engine.KeyShape
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.port.Availability
import io.github.junekim0007.cryptobench.preparation.port.DeviceCapability

class KeyPlanner(
    private val capability: DeviceCapability,
    private val engineTypes: EngineTypes = EngineTypes.standard(),
) {

    fun plan(case: BenchmarkCase): KeyRecipe {
        val names = KeyAlgorithmName.candidates(case.type, case.algorithm)
        val algorithm = names.first().algorithm
        return when (engineTypes.of(case.type).keyShape) {
            KeyShape.NONE -> KeyRecipe.None
            KeyShape.SECRET -> names.firstNotNullOfOrNull { secret(case, it) } ?: unavailable(SECRET_GENERATOR, algorithm)
            KeyShape.PAIR -> names.firstNotNullOfOrNull { pair(case, it, count = 1) } ?: unavailable(PAIR_GENERATOR, algorithm)
            KeyShape.PEER_PAIRS -> names.firstNotNullOfOrNull { pair(case, it, count = 2) } ?: unavailable(PAIR_GENERATOR, algorithm)
            KeyShape.DEVICE_DECIDES -> names.firstNotNullOfOrNull { secret(case, it) } ?: names.firstNotNullOfOrNull { pair(case, it, count = 1) }
                ?: KeyRecipe.Unavailable("no_key_generator: $algorithm")
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
