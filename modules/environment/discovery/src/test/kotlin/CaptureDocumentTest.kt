package io.github.junekim0007.cryptobench.discovery

import io.github.junekim0007.cryptobench.discovery.adapter.ProviderProbe
import io.github.junekim0007.cryptobench.discovery.contract.CapturedEnvironment
import io.github.junekim0007.cryptobench.discovery.contract.RuntimeInfo
import io.github.junekim0007.cryptobench.discovery.write.CaptureDocument
import io.github.junekim0007.cryptobench.discovery.write.YamlCodec
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test
import java.security.Security

/** Encode and decode live on one object so a key renamed on one side fails here, not in a reader. */
class CaptureDocumentTest {

    private val capture = CAPTURE

    @Test
    fun roundTripsThroughTheDocumentAndThroughYaml() {
        val codec = YamlCodec()
        assertEquals(capture, CaptureDocument.parse(CaptureDocument.of(capture)))
        assertEquals(capture, CaptureDocument.parse(codec.load(codec.dump(CaptureDocument.of(capture)))))
    }

    @Test
    fun refusesAndNamesWhatIsWrong() {
        val damages: List<Pair<(MutableMap<String, Any>) -> Unit, String>> = listOf(
            { document: MutableMap<String, Any> -> document[CaptureDocument.SCHEMA_VERSION] = CapturedEnvironment.SCHEMA_VERSION + 1 } to "unsupported_schema_version: 2, this build reads 1",
            { document: MutableMap<String, Any> -> document.remove(CaptureDocument.PROVIDERS); Unit } to "missing_field: providers",
            { document: MutableMap<String, Any> -> document[CaptureDocument.RUNTIME] = "not a section" } to "wrong_type: runtime",
        )
        damages.forEach { (damage, expected) ->
            val document = LinkedHashMap(CaptureDocument.of(capture)).also(damage)
            val error = assertThrows(IllegalArgumentException::class.java) { CaptureDocument.parse(document) }
            assertEquals(expected, error.message)
        }
    }

    /** jdk.security.defaultKeySize changes default key sizes per machine with no code change, so the capture records it; older captures without it still read. */
    @Test
    fun theDefaultKeySizePropertyIsRecordedAndOptional() {
        val before = System.getProperty(RuntimeInfo.DEFAULT_KEY_SIZE_PROPERTY)
        try {
            System.setProperty(RuntimeInfo.DEFAULT_KEY_SIZE_PROPERTY, "RSA:2048,EC:256")
            val runtime = RuntimeInfo()
            assertEquals("RSA:2048,EC:256", runtime.defaultKeySizeProperty)
            val document = CaptureDocument.of(capture.copy(runtime = runtime))
            assertEquals("RSA:2048,EC:256", (document[CaptureDocument.RUNTIME] as Map<*, *>)[CaptureDocument.DEFAULT_KEY_SIZE_PROPERTY])
        } finally {
            if (before == null) System.clearProperty(RuntimeInfo.DEFAULT_KEY_SIZE_PROPERTY) else System.setProperty(RuntimeInfo.DEFAULT_KEY_SIZE_PROPERTY, before)
        }
        val document = LinkedHashMap(CaptureDocument.of(capture))
        document[CaptureDocument.RUNTIME] = LinkedHashMap(document[CaptureDocument.RUNTIME] as Map<*, *>).apply { remove(CaptureDocument.DEFAULT_KEY_SIZE_PROPERTY) }
        assertEquals("", CaptureDocument.parse(document).runtime.defaultKeySizeProperty)
    }

    private companion object {
        val CAPTURE = ProviderProbe().capture(
            Security.getProviders(),
            RuntimeInfo(model = "Pixel 9", manufacturer = "Google", hardware = "zuma", sdkInt = 37, release = "17"),
            capturedAtMillis = 1_700_000_000_000L,
        )
    }
}
