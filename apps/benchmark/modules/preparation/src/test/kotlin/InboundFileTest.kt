package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.inbound.InboundFile
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

class InboundFileTest {

    private fun rejection(text: String): String =
        assertThrows(RuntimeException::class.java) { InboundFile.read("effective.yaml", text) }.message!!

    /** Every refusal names the file, so a failed run says which input to fix. */
    @Test
    fun aBadFileIsRefusedByName() {
        assertEquals("missing_field: effective.yaml: policy", rejection(EffectiveFixture.TEXT.replace("policy: {onFailure: skip}\n", "")))
        assertEquals("unsupported_schema_version: effective.yaml: 1, this build reads 2", rejection(EffectiveFixture.TEXT.replace("schemaVersion: 2", "schemaVersion: 1")))
        assertTrue(rejection(EffectiveFixture.TEXT.replace("  seed: 0\n", "  seed: 0\n  seed: 1\n")).contains("duplicate key"))
        assertTrue(rejection("\tbroken: [\n").startsWith("unreadable_yaml: effective.yaml:"))
        assertTrue(rejection(EffectiveFixture.TEXT.replace("policy: {", "polcy: {}\npolicy: {")).startsWith("unknown_keys: effective.yaml: effective [polcy],"))
        assertEquals("missing_file: /no/such/effective.yaml",
            assertThrows(IllegalArgumentException::class.java) { InboundFile.read(File("/no/such/effective.yaml")) }.message)
    }
}
