package io.github.junekim0007.cryptobench.discovery.contract

/** What actually instantiated, for the capture taken at the same instant; carries no timing. */
data class TrialReport(
    val capturedAtMillis: Long,
    val services: List<ServiceTrialEntry> = emptyList(),
    val schemaVersion: Int = SCHEMA_VERSION,
) {

    companion object {
        const val SCHEMA_VERSION = 1
    }
}
