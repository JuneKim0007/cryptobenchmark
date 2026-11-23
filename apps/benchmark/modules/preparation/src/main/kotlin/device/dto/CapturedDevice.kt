package io.github.junekim0007.cryptobench.preparation.device.dto

import io.github.junekim0007.cryptobench.contract.capture.CapturedEnvironment
import io.github.junekim0007.cryptobench.document.catalogue.CatalogueOverlays

data class CapturedDevice(
    // in precedence order: the contract refuses a capture listing them otherwise
    val providers: List<CapturedProvider>,
    // runtime.sdkInt of an Android capture; null on a JVM, whose capture records 0
    val sdkInt: Int?,
    // the guide's name for where it ran: android-<sdk>, else jdk-<major>
    val platform: String?,
) {

    companion object {
        fun of(capture: CapturedEnvironment): CapturedDevice {
            val sdkInt = capture.runtime.sdkInt.takeIf { it > 0 }
            return CapturedDevice(
                providers = capture.providers.map { provider ->
                    CapturedProvider(provider.name, provider.services.map { CapturedService(it.type, it.algorithm, it.aliases) })
                },
                sdkInt = sdkInt,
                platform = CatalogueOverlays.platform(sdkInt, capture.runtime.javaVersion),
            )
        }
    }
}
