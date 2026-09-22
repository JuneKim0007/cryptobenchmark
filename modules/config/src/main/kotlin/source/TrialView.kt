package io.github.junekim0007.cryptobench.config.source

data class TrialView(
    val capturedAtMillis: Long,
    val entries: List<Entry>,
    val defaultRunInputSize: Int? = null,
) {

    data class Entry(
        val provider: String,
        val type: String,
        val name: String,
        val run: DefaultRun,
    )

    data class DefaultRun(
        val works: Boolean,
        val keyAlgorithm: String = "",
        val keyProvider: String = "",
        val keySize: Int? = null,
        val inputSize: Int? = null,
        val providerChose: String = "",
        val bareName: Boolean = false,
        val error: String = "",
    )
}
