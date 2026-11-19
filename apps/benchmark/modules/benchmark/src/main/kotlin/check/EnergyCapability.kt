package io.github.junekim0007.cryptobench.benchmark.check

import io.github.junekim0007.cryptobench.document.SchemaVersion
import io.github.junekim0007.cryptobench.benchmark.report.CaseDocument
import io.github.junekim0007.cryptobench.files.FileNames

// Rails reporting equal energy for idle and busy windows measure nothing (an emulator HAL counts polls).
data class EnergyCapability(
    val railsPresent: Boolean,
    val railsResponsive: Boolean,
    val idleMicrojoules: Double,
    val busyMicrojoules: Double,
    val windowSeconds: Double,
    val acceptUnresponsive: Boolean,
) {

    fun refusal(): String? = when {
        !railsPresent -> "no_power_rails: the device reports no power rails"
        !railsResponsive && !acceptUnresponsive ->
            "rails_unresponsive: idle ${idleMicrojoules} uJ, busy ${busyMicrojoules} uJ over ${windowSeconds} s"
        else -> null
    }

    companion object {

        fun parse(text: String): EnergyCapability {
            val document = CaseDocument.load(text)
            SchemaVersion.require(document, 1, FileNames.ENERGY_CAPABILITY)
            fun flag(key: String) = document[key] as? Boolean ?: throw IllegalArgumentException("missing_field: ${FileNames.ENERGY_CAPABILITY} $key")
            fun number(key: String) = (document[key] as? Number)?.toDouble() ?: throw IllegalArgumentException("missing_field: ${FileNames.ENERGY_CAPABILITY} $key")
            return EnergyCapability(flag("railsPresent"), flag("railsResponsive"), number("idleMicrojoules"),
                                    number("busyMicrojoules"), number("windowSeconds"), flag("acceptUnresponsive"))
        }
    }
}
