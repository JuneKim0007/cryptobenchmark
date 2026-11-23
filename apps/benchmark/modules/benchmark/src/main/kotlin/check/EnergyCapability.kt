package io.github.junekim0007.cryptobench.benchmark.check

import io.github.junekim0007.cryptobench.document.YamlCodec
import io.github.junekim0007.cryptobench.document.versioned.DocumentReader
import io.github.junekim0007.cryptobench.document.versioned.YamlFiles
import io.github.junekim0007.cryptobench.files.FileNames
import java.io.File

// Rails reporting equal energy for idle and busy windows measure nothing (an emulator HAL counts polls).
data class EnergyCapability(
    val railsPresent: Boolean,
    val railsResponsive: Boolean,
    val idleMicrojoules: Double,
    val busyMicrojoules: Double,
    val idleWindowSeconds: Double,
    val busyWindowSeconds: Double,
    val acceptUnresponsive: Boolean,
) {

    fun refusal(): String? = when {
        !railsPresent -> "no_power_rails: the device reports no power rails"
        !railsResponsive && !acceptUnresponsive ->
            "rails_unresponsive: idle ${idleMicrojoules} uJ over ${idleWindowSeconds} s, busy ${busyMicrojoules} uJ over ${busyWindowSeconds} s"
        else -> null
    }

    companion object : DocumentReader<EnergyCapability> {

        private const val SCHEMA_VERSION = 4

        override val schemaVersion = SCHEMA_VERSION

        fun parse(text: String): EnergyCapability = YamlFiles(YamlCodec.RESULTS).readOnly(File(FileNames.ENERGY_CAPABILITY), this).read(text)

        override fun parse(document: Map<String, Any>): EnergyCapability {
            fun flag(key: String) = document[key] as? Boolean ?: throw IllegalArgumentException("missing_field: $key")
            fun number(key: String) = (document[key] as? Number)?.toDouble() ?: throw IllegalArgumentException("missing_field: $key")
            return EnergyCapability(flag("railsPresent"), flag("railsResponsive"), number("idleMicrojoules"),
                                    number("busyMicrojoules"), number("idleWindowSeconds"), number("busyWindowSeconds"),
                                    flag("acceptUnresponsive"))
        }
    }
}
