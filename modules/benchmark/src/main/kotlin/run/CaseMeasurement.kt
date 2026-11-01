package io.github.junekim0007.cryptobench.benchmark.run

import io.github.junekim0007.cryptobench.benchmark.report.MetricSamples
import io.github.junekim0007.cryptobench.benchmark.report.ResultRow
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase

class CaseMeasurement(val case: BenchmarkCase, val keyKind: String?, val time: MetricSamples, val parameters: Map<String, Any> = emptyMap()) {

    constructor(case: BenchmarkCase, keyKind: String?, iterations: Int, nanosPerOperation: List<Double>, parameters: Map<String, Any> = emptyMap()) :
        this(case, keyKind, MetricSamples(nanosPerOperation, iterations), parameters)

    val iterations: Int get() = time.iterations

    val nanosPerOperation: List<Double> get() = time.runs

    val medianNanos: Double
        get() {
            val sorted = time.runs.sorted()
            val middle = sorted.size / 2
            return if (sorted.size % 2 == 1) sorted[middle] else (sorted[middle - 1] + sorted[middle]) / 2.0
        }

    fun row(): ResultRow = ResultRow(
        id = case.id,
        type = case.type,
        algorithm = case.algorithm,
        provider = case.provider,
        operation = case.operation.name,
        keySize = case.keySize,
        inputSize = case.inputSize,
        keyKind = keyKind,
        metrics = linkedMapOf(MetricSamples.TIME to time),
        parameters = parameters,
    )
}
