package io.github.junekim0007.cryptobench.preparation.resolve

import io.github.junekim0007.cryptobench.preparation.global.GlobalSettings
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.operation.OperationDefinition
import io.github.junekim0007.cryptobench.preparation.operation.OperationDefinitions
import io.github.junekim0007.cryptobench.preparation.request.Selection

internal object SelectionExpander {

    fun expand(global: GlobalSettings, selection: Selection, providers: List<String>, operations: List<Operation>): List<BenchmarkCase> {
        val cases = mutableListOf<BenchmarkCase>()
        for (provider in providers) {
            for (operation in selection.operations.ifEmpty { operations }.toList()) {
                val definition = OperationDefinitions.of(operation)
                for (keySize in keySizesFor(definition, selection)) {
                    for (inputSize in inputSizesFor(definition, selection, global)) {
                        for (phase in global.phases) {
                            cases += BenchmarkCase(
                                type = selection.type,
                                algorithm = selection.algorithm,
                                group = selection.group,
                                provider = provider,
                                operation = operation,
                                keySize = keySize,
                                inputSize = inputSize,
                                phase = phase,
                                metrics = global.metrics,
                                seed = global.seed,
                                harness = global.harness.mergedWith(selection.harness),
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

    /** A key size is an axis only for an operation that takes one and an entry that names some. */
    private fun keySizesFor(definition: OperationDefinition, selection: Selection): List<Int?> =
        if (definition.consumesKeySize && selection.keySizes.isNotEmpty()) selection.keySizes else listOf(null)

    /** An input size is an axis only for an operation that consumes input; a case built without a list gets the run's. */
    private fun inputSizesFor(definition: OperationDefinition, selection: Selection, global: GlobalSettings): List<Int?> =
        if (definition.consumesInput) global.inputSizesFor(selection.inputSizes) else listOf(null)
}
