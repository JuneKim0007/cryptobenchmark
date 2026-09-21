package io.github.junekim0007.cryptobench.discovery.contract

/** One real call with a default key: what ran, with which key, and what the provider chose on its own. */
data class DefaultRunOutcome(
    val works: Boolean,
    val keyAlgorithm: String = "",
    val keyProvider: String = "",
    val keySize: Int? = null,
    val inputSize: Int? = null,
    val providerChose: String = "",
    val bareName: Boolean = false,
    val error: String = "",
) {

    init {
        require(works == error.isEmpty()) { "an outcome carries an error exactly when it fails" }
        require(keySize == null || keySize > 0) { "not_positive: keySize $keySize" }
        require(inputSize == null || inputSize >= 0) { "negative: inputSize $inputSize" }
    }

    companion object {

        fun failure(throwable: Throwable): DefaultRunOutcome =
            DefaultRunOutcome(works = false, error = throwable.javaClass.simpleName + ": " + throwable.message.orEmpty())
    }
}
