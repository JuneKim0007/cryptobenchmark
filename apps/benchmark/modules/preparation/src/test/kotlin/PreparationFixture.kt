package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.port.Availability
import io.github.junekim0007.cryptobench.preparation.port.DeviceCapability
import io.github.junekim0007.cryptobench.preparation.record.PreparedFile
import io.github.junekim0007.cryptobench.preparation.report.SkipFile
import java.io.File
import java.nio.file.Files

/** One small device and one effective file, shared by the preparation tests. */
internal class PreparationFixture {

    val directory: File = Files.createTempDirectory("preparation").toFile()

    /** SunJCE really generates AES; "Serpent" is claimed by this device but no provider on the JVM can make its key. */
    val device = object : DeviceCapability {
        private val serves = mapOf(
            "SunJCE" to setOf("Cipher/AES/GCM/NoPadding", "KeyGenerator/AES", "Cipher/Serpent/CBC/NoPadding", "KeyGenerator/Serpent", "Cipher/AES_128/GCM/NoPadding"),
            "SUN" to setOf("MessageDigest/SHA-256"),
        )
        override fun providers(): List<String> = listOf("SunJCE", "SUN")
        override fun check(provider: String, type: String, algorithm: String): Availability =
            if ("$type/$algorithm" in serves[provider].orEmpty()) Availability.Available else Availability.Unavailable("not_registered")
    }

    fun effective(onFailure: String) = File(directory, "effective.yaml").apply {
        writeText("""
schemaVersion: 1
generatedFrom: {global: g, testSet: t, inventory: i, capture: c, trial: t, device: {}}
run: {inputSizes: [64, 1024], phases: [WARM], metrics: [TIME], processRepetitions: 3, seed: 0}
policy: {onFailure: $onFailure}
providers:
  SunJCE:
    Cipher:
      AES/GCM/NoPadding:
        keySizes: [128]
        parameters: {class: javax.crypto.spec.GCMParameterSpec, arguments: [128, fresh(12)]}
      Serpent/CBC/NoPadding: {keySizes: [128]}
      ChaCha20: {}
  SUN:
    MessageDigest:
      SHA-256: {}
skipped: []
""".trimIndent())
    }

    val preparation = Preparation(device, SkipFile(File(directory, "preparation")), PreparedFile(File(directory, "preparation")))
}
