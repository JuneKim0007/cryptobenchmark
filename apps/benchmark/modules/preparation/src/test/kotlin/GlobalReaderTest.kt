package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.global.GlobalReader
import io.github.junekim0007.cryptobench.preparation.global.OnFailure
import io.github.junekim0007.cryptobench.preparation.inbound.InboundFile
import io.github.junekim0007.cryptobench.preparation.measurement.Phase
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

class GlobalReaderTest {

    private fun global(text: String = EffectiveFixture.TEXT) = GlobalReader.read(InboundFile.read("effective.yaml", text))

    @Test
    fun runAndPolicyAreReadTogether() {
        val global = global()
        assertEquals(listOf(1024), global.inputSizes)
        assertEquals(setOf(Phase.WARM, Phase.COLD), global.phases)
        assertEquals(3, global.processRepetitions)
        assertEquals(OnFailure.SKIP, global.onFailure)
    }

    @Test
    fun namesAChoiceOutsideTheEnum() {
        assertEquals("unknown_onFailure: retry, one of [STOP, SKIP]",
            assertThrows(IllegalArgumentException::class.java) { global(EffectiveFixture.TEXT.replace("onFailure: skip", "onFailure: retry")) }.message)
        assertEquals("unknown_phase: HOT, one of [WARM, COLD]",
            assertThrows(IllegalArgumentException::class.java) { global(EffectiveFixture.TEXT.replace("phases: [WARM, COLD]", "phases: [HOT]")) }.message)
    }
}
