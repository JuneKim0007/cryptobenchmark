package io.github.junekim0007.cryptobench.contract.trial

/** One key generated inside a keystore provider on one hardware path; error is the coded refusal. */
data class KeystoreRow(
    val provider: String,
    val type: String,
    val algorithm: String,
    val backing: String,
    val keySize: Int? = null,
    val curve: String = "",
    val supported: Boolean,
    val error: String = "",
    val millis: Long = 0,
) {

    init {
        require(supported == error.isEmpty()) { "a row carries an error exactly when it is refused" }
        require(backing in BACKINGS) { "invalid: backing $backing, one of $BACKINGS" }
        require(keySize == null || curve.isEmpty()) { "a row names a key size or a curve, not both" }
    }

    companion object {
        const val TEE = "tee"
        const val STRONGBOX = "strongbox"
        val BACKINGS = listOf(TEE, STRONGBOX)
    }
}

/** The keystore trial: its rows, or why it did not run on this runtime. */
data class KeystoreSection(val rows: List<KeystoreRow> = emptyList(), val absent: String = "") {

    init {
        require(absent.isEmpty() || rows.isEmpty()) { "an absent section holds no rows" }
    }
}
