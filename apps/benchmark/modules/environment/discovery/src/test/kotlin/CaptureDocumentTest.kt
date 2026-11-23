package io.github.junekim0007.cryptobench.discovery

import io.github.junekim0007.cryptobench.discovery.adapter.DeviceRuntimeReader
import io.github.junekim0007.cryptobench.discovery.adapter.ProviderProbe
import io.github.junekim0007.cryptobench.contract.capture.ProviderOrigin
import io.github.junekim0007.cryptobench.contract.capture.RuntimeInfo
import io.github.junekim0007.cryptobench.contract.capture.CaptureDocument
import io.github.junekim0007.cryptobench.discovery.write.EnvironmentYamlWriter
import io.github.junekim0007.cryptobench.discovery.write.ProbeDirectory
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test
import java.nio.file.Files
import java.security.Security

/** Encode and decode live on one object so a key renamed on one side fails here, not in a reader. */
class CaptureDocumentTest {

    private val capture = CAPTURE

    @Test
    fun roundTripsThroughTheDocumentAndThroughTheWrittenFile() {
        assertEquals(capture, CaptureDocument.parse(CaptureDocument.of(capture)))
        val folder = Files.createTempDirectory("capture").toFile()
        assertEquals(capture, CaptureDocument.read(EnvironmentYamlWriter(ProbeDirectory(folder)).write(capture)))
        folder.deleteRecursively()
    }

    @Test
    fun refusesAndNamesWhatIsWrong() {
        val damages: List<Pair<(MutableMap<String, Any>) -> Unit, String>> = listOf(
            { document: MutableMap<String, Any> -> document.remove("providers"); Unit } to "missing_field: providers",
            { document: MutableMap<String, Any> -> document["runtime"] = "not a section" } to "wrong_type: runtime",
            { document: MutableMap<String, Any> -> document["providers"] = providersWithout(document, "origin") } to "missing_field: origin",
            { document: MutableMap<String, Any> -> document["runtime"] = LinkedHashMap(document["runtime"] as Map<*, *>).apply { remove("fingerprint") } } to "missing_field: fingerprint",
            { document: MutableMap<String, Any> -> document["providers"] = (document["providers"] as List<*>).reversed() } to "invalid: providers precedence",
            { document: MutableMap<String, Any> -> document["providers"] = (document["providers"] as List<*>).let { it + it.last() } } to "invalid: providers precedence",
            { document: MutableMap<String, Any> -> document["providers"] = renumbered(document) { it + 1 } } to "invalid: providers precedence [2, ",
            { document: MutableMap<String, Any> -> document["providers"] = renumbered(document) { it - 1 } } to "invalid: providers precedence [0, ",
            { document: MutableMap<String, Any> -> document["providers"] = renumbered(document) { if (it == 1) 1 else it + 1 } } to "invalid: providers precedence [1, 3, ",
        )
        damages.forEach { (damage, expected) ->
            val document = LinkedHashMap(CaptureDocument.of(capture)).also(damage)
            val error = assertThrows(IllegalArgumentException::class.java) { CaptureDocument.parse(document) }
            assertTrue(error.message!!, error.message!!.startsWith(expected))
        }
    }

    /** jdk.security.defaultKeySize changes default key sizes per machine with no code change, so the capture records it. */
    @Test
    fun theDefaultKeySizePropertyIsRecorded() {
        val before = System.getProperty(DeviceRuntimeReader.DEFAULT_KEY_SIZE_PROPERTY)
        try {
            System.setProperty(DeviceRuntimeReader.DEFAULT_KEY_SIZE_PROPERTY, "RSA:2048,EC:256")
            val runtime = DeviceRuntimeReader.read()
            assertEquals("RSA:2048,EC:256", runtime.defaultKeySizeProperty)
            val document = CaptureDocument.of(capture.copy(runtime = runtime))
            assertEquals("RSA:2048,EC:256", (document["runtime"] as Map<*, *>)["defaultKeySizeProperty"])
        } finally {
            if (before == null) System.clearProperty(DeviceRuntimeReader.DEFAULT_KEY_SIZE_PROPERTY) else System.setProperty(DeviceRuntimeReader.DEFAULT_KEY_SIZE_PROPERTY, before)
        }
    }

    @Test
    fun theBuildIdentityIsReadOnAJvmAndRecorded() {
        val runtime = DeviceRuntimeReader.read()
        assertEquals("", runtime.fingerprint)
        assertEquals(System.getProperty("java.vendor"), runtime.javaVendor)
        assertEquals(System.getProperty("java.runtime.version"), runtime.javaRuntimeVersion)
        assertEquals(System.getProperty("os.name"), runtime.osName)
        assertEquals(System.getProperty("os.arch"), runtime.osArch)
        val document = LinkedHashMap(CaptureDocument.of(capture.copy(runtime = runtime.copy(fingerprint = "a/b/c:17/X/1:user/release-keys"))))
        assertEquals("a/b/c:17/X/1:user/release-keys", CaptureDocument.parse(document).runtime.fingerprint)
    }

    @Test
    fun aBundledProviderRoundTripsWithItsOriginAndArtifact() {
        val bundled = capture.copy(providers = capture.providers.take(1).map { it.copy(origin = ProviderOrigin.BUNDLED, artifact = "g:n:1") })
        val document = CaptureDocument.of(bundled)
        assertEquals("bundled", ((document["providers"] as List<*>).single() as Map<*, *>)["origin"])
        assertEquals(bundled, CaptureDocument.parse(document))
    }

    private fun providersWithout(document: Map<String, Any>, key: String): List<Map<*, *>> =
        (document["providers"] as List<*>).map { LinkedHashMap(it as Map<*, *>).apply { remove(key) } }

    private fun renumbered(document: Map<String, Any>, precedence: (Int) -> Int): List<Map<*, *>> =
        (document["providers"] as List<*>).map { provider -> LinkedHashMap(provider as Map<String, Any>).apply { put("precedence", precedence(get("precedence") as Int)) } }

    private companion object {
        val CAPTURE = ProviderProbe().capture(
            Security.getProviders(),
            RuntimeInfo(model = "Pixel 9", manufacturer = "Google", hardware = "zuma", sdkInt = 37, release = "17"),
            capturedAtMillis = 1_700_000_000_000L,
        )
    }
}
