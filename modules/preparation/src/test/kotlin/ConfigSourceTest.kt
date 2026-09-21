package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.measurement.Phase
import io.github.junekim0007.cryptobench.preparation.port.Availability
import io.github.junekim0007.cryptobench.preparation.port.DeviceCapability
import io.github.junekim0007.cryptobench.preparation.request.OnFailure
import io.github.junekim0007.cryptobench.preparation.request.Selection
import io.github.junekim0007.cryptobench.preparation.resolve.CaseResolver
import io.github.junekim0007.cryptobench.preparation.source.ConfigSource
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test

/** The fixture is effective.yaml in the shape the config module writes it; a key renamed there must fail here. */
class ConfigSourceTest {

    private val source = ConfigSource()

    private fun rejection(text: String): String? =
        assertThrows(RuntimeException::class.java) { source.read(text) }.message

    @Test
    fun everyEntryBecomesASelectionPinnedToItsProvider() {
        val request = source.read(DEFAULT_YAML)
        assertEquals(
            listOf(
                Selection("MessageDigest", "SHA-256", providers = listOf("SUN")),
                Selection("Cipher", "AES/CBC/PKCS5PADDING", providers = listOf("SunJCE"), keySizes = listOf(128, 256), operations = setOf(Operation.DECRYPT)),
                Selection("Cipher", "RSA", providers = listOf("SunJCE"), keySizes = listOf(3072), inputSizes = listOf(32), parameters = OAEP),
            ),
            request.selections,
        )
        assertEquals(listOf(1024), request.inputSizes)
        assertEquals(setOf(Phase.WARM, Phase.COLD), request.phases)
        assertEquals(3, request.processRepetitions)
        assertEquals(OnFailure.SKIP, request.onFailure)
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
        assertEquals("unknown_onFailure: retry, one of [STOP, SKIP]", rejection(DEFAULT_YAML.replace("onFailure: skip", "onFailure: retry")))
        assertEquals("unknown_operation: WRAP, one of [ENCRYPT, DECRYPT, SIGN, VERIFY, DIGEST, COMPUTE_MAC, GENERATE_KEY, GENERATE_KEY_PAIR, AGREE_KEY, TYPE_DEFAULT]", rejection(DEFAULT_YAML.replace("operations: [DECRYPT]", "operations: [WRAP]")))
        assertEquals("unknown_phase: HOT, one of [WARM, COLD]", rejection(DEFAULT_YAML.replace("phases: [WARM, COLD]", "phases: [HOT]")))
        assertEquals("nothing_selected", rejection(DEFAULT_YAML.replace(Regex("(?s)providers:.*?\nskipped:"), "providers: {}\nskipped:")))
        assertEquals("unsupported_config_schema: 2, this build reads 1", rejection(DEFAULT_YAML.replace("schemaVersion: 1", "schemaVersion: 2")))
        assertEquals("wrong_type: SUN.MessageDigest.SHA-256", rejection(DEFAULT_YAML.replace("      SHA-256: {}", "      SHA-256: yes")))
        assertTrue(rejection(DEFAULT_YAML.replace("  seed: 0\n", "  seed: 0\n  seed: 1\n"))!!.contains("duplicate key"))
    }

    private companion object {
        val OAEP: Map<String, Any> = mapOf(
            "class" to "javax.crypto.spec.OAEPParameterSpec",
            "arguments" to listOf("SHA-256", "MGF1", mapOf("field" to "java.security.spec.MGF1ParameterSpec.SHA256"), mapOf("field" to "javax.crypto.spec.PSource\$PSpecified.DEFAULT")),
        )

        const val DEFAULT_YAML = """schemaVersion: 1
generatedFrom:
  global: global.yaml
  testSet: testsets/scope.yaml
  inventory: inventory.yaml
  capture: probe_20260921T204537Z.yaml
  trial: trial_20260921T204537Z.yaml
  device: {model: Pixel 9, manufacturer: Google, hardware: zuma, sdkInt: 37, release: '17', javaVersion: '0'}
run:
  inputSizes: [1024]
  phases: [WARM, COLD]
  metrics: [TIME]
  processRepetitions: 3
  seed: 0
policy: {onFailure: skip}
providers:
  SUN:
    MessageDigest:
      SHA-256: {}
  SunJCE:
    Cipher:
      AES/CBC/PKCS5PADDING:
        keySizes: [128, 256]
        operations: [DECRYPT]
        providerDefaults: [parameters]
      RSA:
        keySizes: [3072]
        inputSizes: [32]
        parameters: {class: javax.crypto.spec.OAEPParameterSpec, arguments: [SHA-256, MGF1, {field: java.security.spec.MGF1ParameterSpec.SHA256}, {field: javax.crypto.spec.PSource${'$'}PSpecified.DEFAULT}]}
        providerDefaults: [keySize, modeAndPadding]
skipped:
- {type: Mac, name: HmacSHA256, reason: 'no_match: nothing on this device matches the include'}
"""
    }
}
