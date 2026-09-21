package io.github.junekim0007.cryptobench.benchmark.preparation.key.plan

import io.github.junekim0007.cryptobench.benchmark.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.benchmark.preparation.port.Availability
import io.github.junekim0007.cryptobench.benchmark.preparation.port.DeviceCapability

/** Case → key recipe. Pure: asks the port, never the JCA. */
class KeyPlanner(
    private val capability: DeviceCapability,
    private val shapes: KeyShapes = KeyShapes.standard(),
) {

    fun plan(case: BenchmarkCase): KeyRecipe {
        val algorithm = KeyAlgorithmName.of(case.type, case.algorithm)
        return when (shapes.of(case.type)) {
            KeyShape.NONE -> KeyRecipe.None
            KeyShape.SECRET -> secret(case, algorithm) ?: unavailable(SECRET_GENERATOR, algorithm)
            KeyShape.PAIR -> pair(case, algorithm, count = 1) ?: unavailable(PAIR_GENERATOR, algorithm)
            KeyShape.PEER_PAIRS -> pair(case, algorithm, count = 2) ?: unavailable(PAIR_GENERATOR, algorithm)
            KeyShape.DEVICE_DECIDES -> secret(case, algorithm) ?: pair(case, algorithm, count = 1)
                ?: KeyRecipe.Unavailable("no_key_generator: $algorithm")
        }
    }

    private fun secret(case: BenchmarkCase, algorithm: String): KeyRecipe.Secret? =
        generatingProvider(case, SECRET_GENERATOR, algorithm)?.let { KeyRecipe.Secret(algorithm, case.keySize, it) }

    private fun pair(case: BenchmarkCase, algorithm: String, count: Int): KeyRecipe.Pair? =
        generatingProvider(case, PAIR_GENERATOR, algorithm)?.let { KeyRecipe.Pair(algorithm, case.keySize, it, count) }

    /** The case's own provider when it can generate the key, else the first in precedence order that can. */
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
