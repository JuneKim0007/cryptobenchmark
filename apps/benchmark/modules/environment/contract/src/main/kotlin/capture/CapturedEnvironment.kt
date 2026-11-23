package io.github.junekim0007.cryptobench.contract.capture

data class CapturedEnvironment(
    val runtime: RuntimeInfo,
    val providers: List<ProviderEntry> = emptyList(),
    val capturedAtMillis: Long = System.currentTimeMillis(),
    val schemaVersion: Int = SCHEMA_VERSION,
    // capturedAtMillis comes from the host on a device run: this is the device's own reading, kept beside it
    val deviceClockMillis: Long = capturedAtMillis,
) {

    init {
        // the list is the precedence order every reader uses as is
        val precedence = providers.map { it.precedence }
        require(precedence.zipWithNext().all { (first, next) -> first < next }) { "invalid: providers precedence $precedence, ascending and unique" }
    }

    companion object {
        const val SCHEMA_VERSION = 1
    }
}
