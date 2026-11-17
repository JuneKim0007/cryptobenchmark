package io.github.junekim0007.cryptobench.preparation.key.plan

import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.operation.KeyShape
import io.github.junekim0007.cryptobench.preparation.operation.OperationDefinitions
import io.github.junekim0007.cryptobench.preparation.operation.SetupCatalog
import io.github.junekim0007.cryptobench.preparation.port.Availability
import io.github.junekim0007.cryptobench.preparation.port.DeviceCapability

/** anyProvider: the interop check's key, shared by two providers anyway, may come from any provider's generator in precedence order. */
class KeyPlanner(
    private val capability: DeviceCapability,
    private val anyProvider: Boolean = false,
) {

    fun plan(case: BenchmarkCase): KeyRecipe {
        val shape = OperationDefinitions.of(case.operation).keyShape
        if (shape == KeyShape.NONE) {
            return KeyRecipe.None
        }
        val measured = capability.measuredKey(case.provider, case.type, case.algorithm)
        val key = case.keySource.algorithm?.let { written -> measured?.takeIf { it.algorithm.equals(written, ignoreCase = true) } ?: KeyCandidate(written) }
            ?: measured ?: return KeyRecipe.Unavailable("no_measured_key: ${case.type}.${case.algorithm}")
        return when (shape) {
            KeyShape.NONE -> KeyRecipe.None
            KeyShape.SECRET -> secret(case, key) ?: unavailable(case, SECRET_GENERATOR, key.algorithm)
            KeyShape.PAIR -> pair(case, key, count = 1) ?: unavailable(case, PAIR_GENERATOR, key.algorithm)
            KeyShape.PEER_PAIRS -> pair(case, key, count = 2) ?: unavailable(case, PAIR_GENERATOR, key.algorithm)
            KeyShape.DEVICE_DECIDES -> secret(case, key) ?: pair(case, key, count = 1)
                ?: KeyRecipe.Unavailable("no_key_generator: ${key.algorithm} in ${case.keySource.label(case.provider)}")
        }
    }

    private fun secret(case: BenchmarkCase, candidate: KeyCandidate): KeyRecipe.Secret? =
        generatingProvider(case, SECRET_GENERATOR, candidate.algorithm)
            ?.let { KeyRecipe.Secret(candidate.algorithm, case.keySize ?: candidate.keySize, it, case.keyParameters) }

    private fun pair(case: BenchmarkCase, candidate: KeyCandidate, count: Int): KeyRecipe.Pair? =
        generatingProvider(case, PAIR_GENERATOR, candidate.algorithm)
            ?.let { KeyRecipe.Pair(candidate.algorithm, case.keySize ?: candidate.keySize, it, count, case.keyParameters) }

    // a benchmark case: the key source's providers only, another provider's generator only when the entry names it or `any`
    private fun generatingProvider(case: BenchmarkCase, generatorType: String, algorithm: String): String? =
        (case.keySource.providers(case.provider, capability.providers()) + if (anyProvider) capability.providers() else emptyList()).distinct()
            .firstOrNull { capability.check(it, generatorType, algorithm) == Availability.Available }

    private fun unavailable(case: BenchmarkCase, generatorType: String, algorithm: String): KeyRecipe.Unavailable =
        KeyRecipe.Unavailable("no_key_generator: $generatorType.$algorithm in ${case.keySource.label(case.provider)}")

    private companion object {
        val SECRET_GENERATOR: String by lazy { SetupCatalog.standard.generator(SetupCatalog.SECRET_KEY) }
        val PAIR_GENERATOR: String by lazy { SetupCatalog.standard.generator(SetupCatalog.KEY_PAIR) }
    }
}
