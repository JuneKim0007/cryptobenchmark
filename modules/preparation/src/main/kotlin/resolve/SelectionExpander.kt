package io.github.junekim0007.cryptobench.preparation.resolve

import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.request.BenchmarkRequest
import io.github.junekim0007.cryptobench.preparation.request.Selection

internal object SelectionExpander {

    /** provider × key size × input size × phase, dropping the axes the type is not measured along. */
    fun expand(request: BenchmarkRequest, selection: Selection, providers: List<String>, rule: AxisRule): List<BenchmarkCase> {
        val keySizes: List<Int?> = if (rule.usesKeySize && selection.keySizes.isNotEmpty()) selection.keySizes else listOf(null)
        val inputSizes: List<Int?> = if (rule.usesInputSize) selection.inputSizes.ifEmpty { request.inputSizes } else listOf(null)
        return providers.flatMap { provider ->
            keySizes.flatMap { keySize ->
                inputSizes.flatMap { inputSize ->
                    request.phases.map { phase ->
                        BenchmarkCase(
                            type = selection.type,
                            algorithm = selection.algorithm,
                            provider = provider,
                            keySize = keySize,
                            inputSize = inputSize,
                            phase = phase,
                            metrics = request.metrics,
                            seed = request.seed,
                            keyParameters = selection.keyParameters,
                            parameters = selection.parameters,
                        )
                    }
                }
            }
        }
    }
}
