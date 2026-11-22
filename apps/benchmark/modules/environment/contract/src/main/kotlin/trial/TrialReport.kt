package io.github.junekim0007.cryptobench.contract.trial

data class TrialReport(
    val capturedAtMillis: Long,
    val services: List<ServiceTrialEntry> = emptyList(),
    val schemaVersion: Int = SCHEMA_VERSION,
    val defaultRunInputSize: Int? = null,
    val keystore: KeystoreSection? = null,
) {

    companion object {
        const val SCHEMA_VERSION = 3
    }
}
