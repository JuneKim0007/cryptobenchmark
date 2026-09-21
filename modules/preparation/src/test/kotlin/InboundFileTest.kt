package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.inbound.InboundFile
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test

class InboundFileTest {

    private fun rejection(text: String): String? =
        assertThrows(RuntimeException::class.java) { InboundFile.read("effective.yaml", text) }.message

    @Test
    fun theSectionsEveryLaterStageNeedsArePresent() {
        assertEquals("effective.yaml", InboundFile.read("effective.yaml", EffectiveFixture.TEXT).fileName)
        assertEquals("missing_field: policy", rejection(EffectiveFixture.TEXT.replace("policy: {onFailure: skip}\n", "")))
    }

    @Test
    fun anotherSchemaIsRefusedWithTheFileName() {
        assertEquals("unsupported_config_schema: effective.yaml: 2, this build reads 1", rejection(EffectiveFixture.TEXT.replace("schemaVersion: 1", "schemaVersion: 2")))
    }

    @Test
    fun aKeyWrittenTwiceIsRefused() {
        assertTrue(rejection(EffectiveFixture.TEXT.replace("  seed: 0\n", "  seed: 0\n  seed: 1\n"))!!.contains("duplicate key"))
    }

    @Test
    fun aMissingOrUnreadableFileIsNamed() {
        val missing = java.io.File("/no/such/effective.yaml")
        assertEquals("missing_file: /no/such/effective.yaml", assertThrows(IllegalArgumentException::class.java) { InboundFile.read(missing) }.message)
        assertTrue(rejection("\tbroken: [\n")!!.startsWith("unreadable_yaml: effective.yaml:"))
    }
}
