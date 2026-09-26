package io.github.junekim0007.cryptobench.benchmark.run

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

    val medianNanos: Long get() = nanosPerOperation.sorted()[nanosPerOperation.size / 2]
}
