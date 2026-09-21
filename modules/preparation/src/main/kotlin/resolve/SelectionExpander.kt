package io.github.junekim0007.cryptobench.preparation.resolve

import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.request.BenchmarkRequest
import io.github.junekim0007.cryptobench.preparation.request.Selection

internal object SelectionExpander {

    fun expand(request: BenchmarkRequest, selection: Selection, providers: List<String>, rule: AxisRule): List<BenchmarkCase> {
        val operations = selection.operations.ifEmpty { rule.operations }.toList()
        val keySizes: List<Int?> = if (rule.usesKeySize && selection.keySizes.isNotEmpty()) selection.keySizes else listOf(null)
        val inputSizes: List<Int?> = if (rule.usesInputSize) selection.inputSizes.ifEmpty { request.inputSizes } else listOf(null)
        val cases = mutableListOf<BenchmarkCase>()
        for (provider in providers) {
            for (operation in operations) {
                for (keySize in keySizes) {
                    for (inputSize in inputSizes) {
                        for (phase in request.phases) {
                            cases += BenchmarkCase(
                                type = selection.type,
                                algorithm = selection.algorithm,
                                provider = provider,
                                operation = operation,
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
        return cases
    }
}
