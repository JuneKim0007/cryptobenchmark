package io.github.junekim0007.cryptobench.config.testset.dto

import io.github.junekim0007.cryptobench.config.harness.HarnessSettings

data class Override(
    val match: Rule,
    val keySizes: List<Int>? = null,
    val inputSizes: List<Int>? = null,
    val key: Map<String, Any>? = null,
    val parameters: Map<String, Any>? = null,
    val operations: List<String>? = null,
    val harness: HarnessSettings? = null,
) {

    init {
        require(keySizes != null || inputSizes != null || key != null || parameters != null || operations != null || harness != null) { "empty_override: $match sets nothing" }
        require(keySizes.orEmpty().all { it > 0 }) { "invalid: keySizes $keySizes" }
        require(inputSizes.orEmpty().all { it > 0 }) { "invalid: inputSizes $inputSizes" }
        require(operations == null || (operations.isNotEmpty() && operations.none { it.isBlank() })) { "invalid: operations $operations" }
    }
}
