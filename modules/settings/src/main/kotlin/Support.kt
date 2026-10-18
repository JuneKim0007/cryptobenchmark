package io.github.junekim0007.cryptobench.settings

/** Whether this device can honour a setting, decided from facts alone, before anything runs. */
sealed interface Support {
    data object Supported : Support
    data class NotSupported(val reason: String) : Support
}

/** A set key the device cannot honour, by its YAML path. */
data class Unsupported(val path: String, val reason: String, val required: Boolean = false) {
    override fun toString(): String = "not_supported: $path: $reason" + if (required) " (required)" else ""
}
