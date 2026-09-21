package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.measurement.Operation

import io.github.junekim0007.cryptobench.preparation.resolve.AxisRule
import io.github.junekim0007.cryptobench.preparation.resolve.AxisRules
import org.junit.Assert.assertEquals
import org.junit.Test

class AxisRulesTest {

    private val rules = AxisRules.standard()

    @Test
    fun theSevenScopedTypesHaveRules() {
        assertEquals(AxisRule(usesKeySize = false, usesInputSize = true, operations = listOf(Operation.DIGEST)), rules.of("MessageDigest"))
        assertEquals(AxisRule(usesKeySize = true, usesInputSize = false, operations = listOf(Operation.GENERATE_KEY_PAIR)), rules.of("keypairgenerator"))
        assertEquals(AxisRule(usesKeySize = true, usesInputSize = true, operations = listOf(Operation.ENCRYPT, Operation.DECRYPT)), rules.of("Cipher"))
    }

    /** A type nobody registered is still measurable; a provider adding engine types must not need a code change. */
    @Test
    fun anUnknownTypeFallsBackToKeyedInput() {
        assertEquals(AxisRule(usesKeySize = true, usesInputSize = true, operations = listOf(Operation.TYPE_DEFAULT)), rules.of("SecretKeyFactory"))
    }

    @Test
    fun withReturnsANewRegistryAndLeavesTheOldOne() {
        val extended = rules.with("SecureRandom", AxisRule(usesKeySize = false, usesInputSize = true, operations = listOf(Operation.TYPE_DEFAULT)))
        assertEquals(AxisRule(usesKeySize = false, usesInputSize = true, operations = listOf(Operation.TYPE_DEFAULT)), extended.of("SecureRandom"))
        assertEquals(AxisRule(usesKeySize = true, usesInputSize = true, operations = listOf(Operation.TYPE_DEFAULT)), rules.of("SecureRandom"))
    }
}
