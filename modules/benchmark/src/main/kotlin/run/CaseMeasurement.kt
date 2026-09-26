package io.github.junekim0007.cryptobench.benchmark.run

import io.github.junekim0007.cryptobench.benchmark.report.ResultRow
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase

class CaseMeasurement(
    val case: BenchmarkCase,
    val iterations: Int,
    val nanosPerOperation: List<Long>,
) {

    init {
        require(iterations >= 1) { "not_positive: iterations $iterations" }
        require(nanosPerOperation.isNotEmpty()) { "missing_field: nanosPerOperation" }
    }

    val medianNanos: Long
        get() {
            val sorted = nanosPerOperation.sorted()
            val middle = sorted.size / 2
            return if (sorted.size % 2 == 1) sorted[middle] else (sorted[middle - 1] + sorted[middle]) / 2
        }

    fun row(): ResultRow = ResultRow(
        id = case.id,
        type = case.type,
        algorithm = case.algorithm,
        provider = case.provider,
        operation = case.operation.name,
        keySize = case.keySize,
        inputSize = case.inputSize,
        iterations = iterations,
        nanosPerOperation = nanosPerOperation,
    )
}
