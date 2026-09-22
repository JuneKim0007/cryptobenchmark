package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.request.BenchmarkRequest
import io.github.junekim0007.cryptobench.preparation.request.Selection
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

class BenchmarkRequestTest {

    private val aes = Selection("Cipher", "AES/GCM/NoPadding", keySizes = listOf(128, 256))

    private fun rejection(block: () -> Any): String? =
        assertThrows(IllegalArgumentException::class.java) { block() }.message

    /** A typo in the request fails here, before a sweep starts, not inside a timed region. */
    @Test
    fun rejectsShapeErrorsByName() {
        assertEquals("missing_field: selections", rejection { BenchmarkRequest(emptyList(), EffectiveFixture.ONE_WARM_RUN) })
        assertEquals("duplicate: selections", rejection { BenchmarkRequest(listOf(aes, aes), EffectiveFixture.ONE_WARM_RUN) })
        assertEquals("not_positive: inputSizes [1024, -1]", rejection { EffectiveFixture.ONE_WARM_RUN.copy(inputSizes = listOf(1024, -1)) })
        assertEquals("not_positive: processRepetitions 0", rejection { EffectiveFixture.ONE_WARM_RUN.copy(processRepetitions = 0) })
        assertEquals("missing_field: algorithm", rejection { Selection("Cipher", "") })
        assertEquals("duplicate: keySizes [128, 128]", rejection { Selection("Cipher", "AES", keySizes = listOf(128, 128)) })
        assertEquals("blank_provider: Cipher/AES", rejection { Selection("Cipher", "AES", providers = listOf("")) })
    }
}
