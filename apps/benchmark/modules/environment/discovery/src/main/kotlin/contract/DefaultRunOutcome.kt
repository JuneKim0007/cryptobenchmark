package io.github.junekim0007.cryptobench.discovery.contract

import io.github.junekim0007.cryptobench.jca.failure.ErrorText

/** One key size a generator was asked for beside its default; refused: it would not make that size. */
data class TriedKey(val size: Int, val keyMaterial: String = "", val keyFormat: String = "", val refused: Boolean = false)

data class DefaultRunOutcome(
    val works: Boolean,
    val keyAlgorithm: String = "",
    val keyProvider: String = "",
    val keySize: Int? = null,
    // a size written into the service name: a contract of that name, not the provider's default
    val fixedKeySize: Int? = null,
    val inputSize: Int? = null,
    val providerChose: String = "",
    val bareName: Boolean = false,
    val keyMaterial: String = "",
    // the generated key's getFormat(), the private key's for a pair; empty when null or not a generator
    val keyFormat: String = "",
    val triedKeys: List<TriedKey> = emptyList(),
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
            DefaultRunOutcome(works = false, error = ErrorText.of(throwable))
    }
}
