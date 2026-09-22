package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.global.GlobalReader
import io.github.junekim0007.cryptobench.preparation.inbound.InboundFile
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.primitive.PrimitiveReader
import io.github.junekim0007.cryptobench.preparation.request.Selection
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

class PrimitiveReaderTest {

    private val inbound = InboundFile.read("effective.yaml", EffectiveFixture.TEXT)

    /** Global is read first and handed in: an entry without input sizes gets global's, here and nowhere later. */
    @Test
    fun entriesAreReadAgainstTheGlobalSettings() {
        val selections = PrimitiveReader.read(inbound, GlobalReader.read(inbound))
        assertEquals(
            listOf(
                Selection("MessageDigest", "SHA-256", providers = listOf("SUN"), inputSizes = listOf(1024)),
                Selection("Cipher", "AES/CBC/PKCS5PADDING", providers = listOf("SunJCE"), keySizes = listOf(128, 256), inputSizes = listOf(1024), operations = setOf(Operation.DECRYPT)),
                Selection("Cipher", "RSA", providers = listOf("SunJCE"), keySizes = listOf(3072), inputSizes = listOf(32), parameters = OAEP),
            ),
            selections,
        )
    }

    /** The same entries read against different global settings resolve differently: the order is load-bearing. */
    @Test
    fun theGlobalSettingsDecideTheFallback() {
        val selections = PrimitiveReader.read(inbound, EffectiveFixture.ONE_WARM_RUN.copy(inputSizes = listOf(64, 16384)))
        assertEquals(listOf(64, 16384), selections.first { it.algorithm == "SHA-256" }.inputSizes)
        assertEquals(listOf(32), selections.first { it.algorithm == "RSA" }.inputSizes)
    }

    @Test
    fun namesWhatIsWrong() {
        fun rejection(text: String) = assertThrows(RuntimeException::class.java) {
            val broken = InboundFile.read("effective.yaml", text)
            PrimitiveReader.read(broken, GlobalReader.read(broken))
        }.message
        assertEquals("unknown_operation: WRAP, one of [ENCRYPT, DECRYPT, SIGN, VERIFY, DIGEST, COMPUTE_MAC, GENERATE_KEY, GENERATE_KEY_PAIR, AGREE_KEY, TYPE_DEFAULT]",
            rejection(EffectiveFixture.TEXT.replace("operations: [DECRYPT]", "operations: [WRAP]")))
        assertEquals("wrong_type: SUN.MessageDigest.SHA-256", rejection(EffectiveFixture.TEXT.replace("      SHA-256: {}", "      SHA-256: yes")))
        assertEquals("nothing_selected: effective.yaml", rejection(EffectiveFixture.TEXT.replace(Regex("(?s)providers:.*?\\nskipped:"), "providers: {}\nskipped:")))
    }

    private companion object {
        val OAEP: Map<String, Any> = mapOf(
            "class" to "javax.crypto.spec.OAEPParameterSpec",
            "arguments" to listOf("SHA-256", "MGF1", mapOf("field" to "java.security.spec.MGF1ParameterSpec.SHA256"), mapOf("field" to "javax.crypto.spec.PSource\$PSpecified.DEFAULT")),
        )
    }
}
