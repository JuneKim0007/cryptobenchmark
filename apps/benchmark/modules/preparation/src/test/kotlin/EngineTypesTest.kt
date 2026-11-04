package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.engine.EngineTypes
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import org.junit.Assert.assertEquals
import org.junit.Test

class EngineTypesTest {

    private val engineTypes = EngineTypes.standard()

    /** A type nobody registered is still measurable; a provider adding engine types must not need a code change. */
    @Test
    fun everyScopedTypeHasItsOperationsAndAnUnknownTypeFallsBack() {
        assertEquals(listOf(Operation.ENCRYPT, Operation.DECRYPT), engineTypes.operationsOf("Cipher"))
        assertEquals(listOf(Operation.DIGEST), engineTypes.operationsOf("MessageDigest"))
        assertEquals(listOf(Operation.GENERATE_KEY_PAIR), engineTypes.operationsOf("keypairgenerator"))
        assertEquals(listOf(Operation.TYPE_DEFAULT), engineTypes.operationsOf("SecretKeyFactory"))
    }

    @Test
    fun withReturnsANewRegistryAndLeavesTheOldOne() {
        val extended = engineTypes.with("SecretKeyFactory", listOf(Operation.GENERATE_KEY))
        assertEquals(listOf(Operation.GENERATE_KEY), extended.operationsOf("SecretKeyFactory"))
        assertEquals(listOf(Operation.TYPE_DEFAULT), engineTypes.operationsOf("SecretKeyFactory"))
    }
}
