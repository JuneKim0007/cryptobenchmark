package io.github.junekim0007.cryptobench.config.testset.dto

/** Values to set on every selected primitive the rule matches. A null field is not set here. */
data class Override(
    val match: Rule,
    val keySizes: List<Int>? = null,
    val inputSizes: List<Int>? = null,
    val key: Map<String, Any>? = null,
    val parameters: Map<String, Any>? = null,
) {

    init {
        require(keySizes != null || inputSizes != null || key != null || parameters != null) { "empty_override: $match sets nothing" }
        require(keySizes.orEmpty().all { it > 0 }) { "invalid: keySizes $keySizes" }
        require(inputSizes.orEmpty().all { it > 0 }) { "invalid: inputSizes $inputSizes" }
    }
}
