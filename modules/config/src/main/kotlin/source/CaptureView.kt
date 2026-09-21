package io.github.junekim0007.cryptobench.config.source

/** The part of environment's probe_<utc>.yaml the configuration needs, read as plain data. */
data class CaptureView(
    val capturedAtMillis: Long,
    val device: Map<String, Any>,
    /** Provider names in precedence order. */
    val providers: List<String>,
)
