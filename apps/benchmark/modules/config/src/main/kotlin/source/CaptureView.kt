package io.github.junekim0007.cryptobench.config.source

data class CaptureView(
    val capturedAtMillis: Long,
    val device: Map<String, Any>,
    val providers: List<String>,
)
