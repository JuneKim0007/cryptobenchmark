package io.github.junekim0007.cryptobench.discovery.contract

data class RequirementReport(
    val capturedAtMillis: Long,
    val deviceClockMillis: Long,
    val services: List<ServiceRequirement> = emptyList(),
    val millis: Long = 0,
    val keyCache: KeyCacheStats = KeyCacheStats(),
    val schemaVersion: Int = SCHEMA_VERSION,
) {

    companion object {
        const val SCHEMA_VERSION = 1
    }
}
