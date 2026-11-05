package io.github.junekim0007.cryptobench.discovery.contract

data class CapturedEnvironment(
    val runtime: RuntimeInfo,
    val providers: List<ProviderEntry> = emptyList(),
    val capturedAtMillis: Long = System.currentTimeMillis(),
    val schemaVersion: Int = SCHEMA_VERSION,
    // capturedAtMillis comes from the host on a device run: this is the device's own reading, kept beside it
    val deviceClockMillis: Long = capturedAtMillis,
) {

    companion object {
        const val SCHEMA_VERSION = 1
    }
}
