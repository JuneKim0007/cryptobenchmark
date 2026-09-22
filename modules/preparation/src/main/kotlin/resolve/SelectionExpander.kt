package io.github.junekim0007.cryptobench.preparation.resolve

import io.github.junekim0007.cryptobench.preparation.engine.EngineType
import io.github.junekim0007.cryptobench.preparation.global.GlobalSettings
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.request.Selection

internal object SelectionExpander {

    fun expand(global: GlobalSettings, selection: Selection, providers: List<String>, engineType: EngineType): List<BenchmarkCase> {
        val cases = mutableListOf<BenchmarkCase>()
        for (provider in providers) {
            for (operation in engineType.operationsFor(selection)) {
                for (keySize in engineType.keySizesFor(selection)) {
                    for (inputSize in engineType.inputSizesFor(selection, global)) {
                        for (phase in global.phases) {
                            cases += BenchmarkCase(
                                type = selection.type,
                                algorithm = selection.algorithm,
                                provider = provider,
                                operation = operation,
                                keySize = keySize,
                                inputSize = inputSize,
                                phase = phase,
                                metrics = global.metrics,
                                seed = global.seed,
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
