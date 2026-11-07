package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.global.GlobalReader
import io.github.junekim0007.cryptobench.settings.HarnessSettings
import io.github.junekim0007.cryptobench.preparation.inbound.InboundFile
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.request.PrimitiveReader
import io.github.junekim0007.cryptobench.preparation.request.Selection
import io.github.junekim0007.cryptobench.preparation.resolve.SelectionExpander
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

class PrimitiveReaderTest {

    private val inbound = InboundFile.read("effective.yaml", EffectiveFixture.TEXT)

    /** An entry keeps only what it states; the run's input sizes are applied once, when cases are expanded. */
    @Test
    fun entriesKeepOnlyWhatTheyState() {
        assertEquals(
            listOf(
                Selection("MessageDigest", "SHA-256", provider = "SUN"),
                Selection("Cipher", "AES/CBC/PKCS5PADDING", provider = "SunJCE", keySizes = listOf(128, 256), operations = setOf(Operation.DECRYPT)),
                Selection("Cipher", "RSA", provider = "SunJCE", keySizes = listOf(3072), inputSizes = listOf(32), parameters = OAEP),
            ),
            PrimitiveReader.read(inbound),
        )
    }

    /** A typo is refused as :config refuses it, instead of the default being measured. */
    @Test
    fun anUnknownEntryKeyIsRefused() {
        val broken = InboundFile.read("effective.yaml", EffectiveFixture.TEXT.replace("        keySizes: [3072]", "        keysizes: [3072]"))
        assertEquals("unknown_keys: SunJCE.Cipher.RSA [keysizes], known [keySizes, inputSizes, key, parameters, operations, providerDefaults, harness]",
            assertThrows(IllegalArgumentException::class.java) { PrimitiveReader.read(broken) }.message)
    }

    @Test
    fun namesWhatIsWrong() {
        fun rejection(text: String) = assertThrows(RuntimeException::class.java) {
            val broken = InboundFile.read("effective.yaml", text)
            PrimitiveReader.read(broken)
        }.message
        assertEquals("unknown_operation", rejection(EffectiveFixture.TEXT.replace("operations: [DECRYPT]", "operations: [WRAP]"))!!.substringBefore(':'))
        assertEquals("wrong_type: SUN.MessageDigest.SHA-256", rejection(EffectiveFixture.TEXT.replace("      SHA-256: {}", "      SHA-256: yes")))
        assertEquals("nothing_selected: effective.yaml", rejection(EffectiveFixture.TEXT.replace(Regex("(?s)providers:.*?\\nskipped:"), "providers: {}\nskipped:")))
    }

    private companion object {
        val OAEP: Map<String, Any> = mapOf(
            "class" to "javax.crypto.spec.OAEPParameterSpec",
            "arguments" to listOf("SHA-256", "MGF1", mapOf("field" to "java.security.spec.MGF1ParameterSpec.SHA256"), mapOf("field" to "javax.crypto.spec.PSource\$PSpecified.DEFAULT")),
        )
    }

    /** One primitive measured twice: the entry key carries the group, the algorithm the device is asked for does not. */
    @Test
    fun anEntryKeyCarriesItsGroup() {
        val text = EffectiveFixture.TEXT.replace("      RSA:\n", "      RSA@oaep256:\n")
        val selections = PrimitiveReader.read(InboundFile.read("effective.yaml", text))
        val rsa = selections.single { it.algorithm == "RSA" }
        assertEquals("oaep256", rsa.group)
        assertEquals("", selections.single { it.algorithm == "SHA-256" }.group)
    }

    /**
     * A setting a run shares lives in one place: an entry states only what differs, so changing the
     * global iterations does not mean editing every entry that never asked for its own.
     */
    @Test
    fun anEntryStatesOnlyTheHarnessSettingsThatDifferFromTheGlobalOnes() {
        val text = EffectiveFixture.TEXT
            .replace("  seed: 0\n", "  seed: 0\n  harness: {iterations: 50, profiling: MethodTracing}\n")
            .replace("      SHA-256: {}", "      SHA-256: {harness: {iterations: 5}}")
        val inbound = InboundFile.read("effective.yaml", text)
        val global = GlobalReader.read(inbound)
        assertEquals(HarnessSettings(iterations = 50, profiling = "MethodTracing"), global.harness)
        val selections = PrimitiveReader.read(inbound)
        val digest = selections.single { it.algorithm == "SHA-256" }
        assertEquals(HarnessSettings(iterations = 5), digest.harness)
        assertEquals(HarnessSettings(), selections.single { it.algorithm == "RSA" }.harness)
        val cases = SelectionExpander.expand(global, digest, listOf(Operation.DIGEST))
        assertEquals(HarnessSettings(iterations = 5, profiling = "MethodTracing"), cases.first().harness)
    }
}
