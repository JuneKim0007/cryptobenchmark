package io.github.junekim0007.cryptobench.benchmark

import io.github.junekim0007.cryptobench.benchmark.preparation.resolve.AxisRule
import io.github.junekim0007.cryptobench.benchmark.preparation.resolve.AxisRules
import org.junit.Assert.assertEquals
import org.junit.Test

class AxisRulesTest {

    private val rules = AxisRules.standard()

    @Test
    fun theSevenScopedTypesHaveRules() {
        assertEquals(AxisRule(usesKeySize = false, usesInputSize = true), rules.of("MessageDigest"))
        assertEquals(AxisRule(usesKeySize = true, usesInputSize = false), rules.of("keypairgenerator"))
        assertEquals(AxisRule(usesKeySize = true, usesInputSize = true), rules.of("Cipher"))
    }

    /** A type nobody registered is still measurable; a provider adding engine types must not need a code change. */
    @Test
    fun anUnknownTypeFallsBackToKeyedInput() {
        assertEquals(AxisRule(usesKeySize = true, usesInputSize = true), rules.of("SecretKeyFactory"))
    }

    @Test
    fun withReturnsANewRegistryAndLeavesTheOldOne() {
        val extended = rules.with("SecureRandom", AxisRule(usesKeySize = false, usesInputSize = true))
        assertEquals(AxisRule(usesKeySize = false, usesInputSize = true), extended.of("SecureRandom"))
        assertEquals(AxisRule(usesKeySize = true, usesInputSize = true), rules.of("SecureRandom"))
    }
}
