package io.github.junekim0007.cryptobench.benchmark

import io.github.junekim0007.cryptobench.benchmark.preparation.measurement.Phase
import io.github.junekim0007.cryptobench.benchmark.preparation.port.Availability
import io.github.junekim0007.cryptobench.benchmark.preparation.port.DeviceCapability
import io.github.junekim0007.cryptobench.benchmark.preparation.request.Selection
import io.github.junekim0007.cryptobench.benchmark.preparation.resolve.CaseResolver
import io.github.junekim0007.cryptobench.benchmark.preparation.source.ConfigSource
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test

/** The fixture is default.yaml in the shape the config module writes it; a key renamed there must fail here. */
class ConfigSourceTest {

    private val source = ConfigSource()

    private fun rejection(text: String): String? =
        assertThrows(RuntimeException::class.java) { source.read(text) }.message

    @Test
    fun enabledEntriesBecomeSelectionsPinnedToTheirProvider() {
        val request = source.read(DEFAULT_YAML)
        assertEquals(
            listOf(
                Selection("MessageDigest", "SHA-256", providers = listOf("SUN")),
                Selection("Cipher", "AES/CBC/PKCS5PADDING", providers = listOf("SunJCE"), keySizes = listOf(128, 256)),
                Selection("Cipher", "RSA", providers = listOf("SunJCE"), keySizes = listOf(3072), inputSizes = listOf(32)),
            ),
            request.selections,
        )
        assertEquals(listOf(1024), request.inputSizes)
        assertEquals(setOf(Phase.WARM, Phase.COLD), request.phases)
        assertEquals(3, request.processRepetitions)
    }

    /** The per-entry input size survives into the cases: RSA runs at 32 bytes while the rest run at 1024. */
    @Test
    fun anEntryInputSizeReachesItsCases() {
        val everything = object : DeviceCapability {
            override fun providers(): List<String> = listOf("SUN", "SunJCE")
            override fun check(provider: String, type: String, algorithm: String): Availability = Availability.Available
        }
        val cases = CaseResolver(everything).resolve(source.read(DEFAULT_YAML)).cases
        assertEquals(setOf(32), cases.filter { it.algorithm == "RSA" }.mapNotNull { it.inputSize }.toSet())
        assertEquals(setOf(1024), cases.filter { it.algorithm != "RSA" }.mapNotNull { it.inputSize }.toSet())
    }

    @Test
    fun namesWhatIsWrong() {
        assertEquals("unknown_phase: HOT, one of [WARM, COLD]", rejection(DEFAULT_YAML.replace("phases: [WARM, COLD]", "phases: [HOT]")))
        assertEquals("nothing_enabled", rejection(DEFAULT_YAML.replace("enabled: true", "enabled: false")))
        assertEquals("unsupported_config_schema: 2, this build reads 1", rejection(DEFAULT_YAML.replace("schemaVersion: 1", "schemaVersion: 2")))
        assertEquals("missing_field: enabled", rejection(DEFAULT_YAML.replace("      SHA-256: {enabled: true}", "      SHA-256: {}")))
        assertTrue(rejection(DEFAULT_YAML.replace("  seed: 0\n", "  seed: 0\n  seed: 1\n"))!!.contains("duplicate key"))
    }

    private companion object {
        const val DEFAULT_YAML = """schemaVersion: 1
generatedFrom:
  capture: probe_20260921T204537Z.yaml
  trial: trial_20260921T204537Z.yaml
  device: {model: Pixel 9, manufacturer: Google, hardware: zuma, sdkInt: 37, release: '17', javaVersion: '0'}
run:
  inputSizes: [1024]
  phases: [WARM, COLD]
  metrics: [TIME]
  processRepetitions: 3
  seed: 0
providers:
  SUN:
    MessageDigest:
      SHA-256: {enabled: true}
      MD2: {enabled: false}
  SunJCE:
    Cipher:
      AES/CBC/PKCS5PADDING:
        enabled: true
        keySizes: [128, 256]
        keyAlgorithm: AES
        keyProvider: SunJCE
        providerChose: AES iv=16B
      RSA:
        enabled: true
        keySizes: [3072]
        inputSizes: [32]
        keyAlgorithm: RSA
        keyProvider: SunRsaSign
        bareName: true
    KeyGenerator:
      SunTlsPrf: {enabled: false, reason: 'IllegalStateException: TlsPrfGenerator must be initialized'}
"""
    }
}
