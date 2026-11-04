package io.github.junekim0007.cryptobench.discovery.contract

data class CapturedEnvironment(
    val runtime: RuntimeInfo,
    val providers: List<ProviderEntry> = emptyList(),
    val capturedAtMillis: Long = System.currentTimeMillis(),
    val schemaVersion: Int = SCHEMA_VERSION,
) {

    companion object {
        const val SCHEMA_VERSION = 1
    }
}
