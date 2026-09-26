package io.github.junekim0007.cryptobench.benchmark.report

class ResultRow(
    val id: String,
    val type: String,
    val algorithm: String,
    val provider: String,
    val operation: String,
    val keySize: Int?,
    val inputSize: Int?,
    val iterations: Int,
    val nanosPerOperation: List<Long>,
) {

    init {
        require(id.isNotBlank()) { "missing_field: id" }
        require(iterations >= 1) { "not_positive: iterations $iterations" }
        require(nanosPerOperation.isNotEmpty()) { "missing_field: nanosPerOperation" }
    }

    fun mergedWith(later: ResultRow): ResultRow {
        require(id == later.id) { "different_case: $id and ${later.id}" }
        return ResultRow(id, type, algorithm, provider, operation, keySize, inputSize, iterations, nanosPerOperation + later.nanosPerOperation)
    }
}
