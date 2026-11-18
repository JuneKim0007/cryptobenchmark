package io.github.junekim0007.cryptobench.config.inventory.dto

/** One row of discovery's keystore trial: a key of this size or curve generated on this path, or the trial's coded refusal. */
data class KeystoreRow(
    val provider: String,
    val type: String,
    val algorithm: String,
    val backing: String,
    val keySize: Int? = null,
    val curve: String = "",
    val supported: Boolean,
    val error: String = "",
) {

    init {
        require(supported == error.isEmpty()) { "a row carries an error exactly when it is refused" }
    }
}
