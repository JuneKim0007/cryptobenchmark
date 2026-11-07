package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.global.GlobalReader
import io.github.junekim0007.cryptobench.preparation.inbound.InboundFile
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test

class GlobalReaderTest {

    private fun global(text: String = EffectiveFixture.TEXT) = GlobalReader.read(InboundFile.read("effective.yaml", text))

    @Test
    fun namesAChoiceOutsideTheEnum() {
        assertEquals("unknown_onFailure",
            assertThrows(IllegalArgumentException::class.java) { global(EffectiveFixture.TEXT.replace("onFailure: skip", "onFailure: retry")) }.message!!.substringBefore(':'))
    }

    /** A typo in run or policy is refused as :config refuses it; host-only run keys are known. */
    @Test
    fun anUnknownRunOrPolicyKeyIsRefused() {
        fun rejection(text: String) = assertThrows(IllegalArgumentException::class.java) { global(text) }.message!!
        assertTrue(rejection(EffectiveFixture.TEXT.replace("  seed: 0\n", "  seed: 0\n  inputsizes: [1]\n")).startsWith("unknown_keys: run [inputsizes],"))
        assertTrue(rejection(EffectiveFixture.TEXT.replace("policy: {onFailure: skip}", "policy: {onFailure: skip, retry: 1}")).startsWith("unknown_keys: policy [retry],"))
        assertEquals(listOf(1024), global(EffectiveFixture.TEXT.replace("  seed: 0\n", "  seed: 0\n  isolation: case\n")).inputSizes)
    }
}
