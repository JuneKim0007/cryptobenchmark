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

    private val capture = ProviderProbe().capture(
        Security.getProviders(),
        RuntimeInfo(model = "Pixel 9", manufacturer = "Google", hardware = "zuma", sdkInt = 37, release = "17"),
        capturedAtMillis = 1_700_000_000_000L,
    )

    @Test
    fun roundTripsThroughTheDocument() {
        assertEquals(capture, CaptureDocument.parse(CaptureDocument.of(capture)))
    }

    @Test
    fun roundTripsThroughYaml() {
        val codec = YamlCodec()
        val text = codec.dump(CaptureDocument.of(capture))
        assertEquals(capture, CaptureDocument.parse(codec.load(text)))
    }

    @Test
    fun rejectsAnotherSchemaVersion() {
        val document = LinkedHashMap(CaptureDocument.of(capture))
        document[CaptureDocument.SCHEMA_VERSION] = CapturedEnvironment.SCHEMA_VERSION + 1
        val error = assertThrows(IllegalArgumentException::class.java) { CaptureDocument.parse(document) }
        assertEquals("unsupported_schema_version: 2, this build reads 1", error.message)
    }

    @Test
    fun namesTheMissingField() {
        val document = LinkedHashMap(CaptureDocument.of(capture))
        document.remove(CaptureDocument.PROVIDERS)
        val error = assertThrows(IllegalArgumentException::class.java) { CaptureDocument.parse(document) }
        assertEquals("missing_field: providers", error.message)
    }

    @Test
    fun namesTheWrongType() {
        val document = LinkedHashMap(CaptureDocument.of(capture))
        document[CaptureDocument.RUNTIME] = "not a section"
        val error = assertThrows(IllegalArgumentException::class.java) { CaptureDocument.parse(document) }
        assertEquals("wrong_type: runtime", error.message)
    }
}
