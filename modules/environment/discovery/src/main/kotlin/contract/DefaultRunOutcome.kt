package io.github.junekim0007.cryptobench.discovery.contract

data class DefaultRunOutcome(
    val works: Boolean,
    val keyAlgorithm: String = "",
    val keyProvider: String = "",
    val keySize: Int? = null,
    val inputSize: Int? = null,
    val providerChose: String = "",
    val bareName: Boolean = false,
    val keyMaterial: String = "",
    // the generated key's getFormat(), the private key's for a pair; empty when null or not a generator
    val keyFormat: String = "",
    val error: String = "",
) {

    init {
        require(works == error.isEmpty()) { "an outcome carries an error exactly when it fails" }
        require(keySize == null || keySize > 0) { "not_positive: keySize $keySize" }
        require(inputSize == null || inputSize >= 0) { "negative: inputSize $inputSize" }
        require(keyMaterial in KEY_MATERIALS) { "unknown_key_material: $keyMaterial" }
    }

    companion object {

        const val EXPORTABLE = "exportable"
        const val NON_EXPORTABLE = "non_exportable"
        private val KEY_MATERIALS = setOf("", EXPORTABLE, NON_EXPORTABLE)

        fun failure(throwable: Throwable): DefaultRunOutcome =
            DefaultRunOutcome(works = false, error = throwable.javaClass.simpleName + ": " + throwable.message.orEmpty())
    }
}
