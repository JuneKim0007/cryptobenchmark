package io.github.junekim0007.cryptobench.preparation.device.dto

data class CapturedDevice(
    val capturedAtMillis: Long,
    val providers: List<CapturedProvider> = emptyList(),
    // runtime.sdkInt of an Android capture; null on a JVM, whose capture records 0
    val sdkInt: Int? = null,
    // the guide's name for where it ran: android-<sdk>, else jdk-<major>
    val platform: String? = null,
)
