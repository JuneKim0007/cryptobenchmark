package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.engine.EngineType
import io.github.junekim0007.cryptobench.preparation.engine.EngineTypes
import io.github.junekim0007.cryptobench.preparation.engine.KeyShape
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import org.junit.Assert.assertEquals
import org.junit.Test

class EngineTypesTest {

    private val engineTypes = EngineTypes.standard()

    private val fallback = EngineType(listOf(Operation.TYPE_DEFAULT), usesKeySize = true, usesInputSize = true, keyShape = KeyShape.DEVICE_DECIDES)

    /** A type nobody registered is still measurable; a provider adding engine types must not need a code change. */
    @Test
    fun everyScopedTypeIsOneRowAndAnUnknownTypeFallsBack() {
        assertEquals(EngineType(listOf(Operation.DIGEST), usesKeySize = false, usesInputSize = true, keyShape = KeyShape.NONE), engineTypes.of("MessageDigest"))
        assertEquals(EngineType(listOf(Operation.GENERATE_KEY_PAIR), usesKeySize = true, usesInputSize = false, keyShape = KeyShape.NONE), engineTypes.of("keypairgenerator"))
        assertEquals(EngineType(listOf(Operation.ENCRYPT, Operation.DECRYPT), usesKeySize = true, usesInputSize = true, keyShape = KeyShape.DEVICE_DECIDES), engineTypes.of("Cipher"))
        assertEquals(fallback, engineTypes.of("SecretKeyFactory"))
    }

    @Test
    fun withReturnsANewRegistryAndLeavesTheOldOne() {
        val row = EngineType(listOf(Operation.TYPE_DEFAULT), usesKeySize = false, usesInputSize = true, keyShape = KeyShape.NONE)
        assertEquals(row, engineTypes.with("SecretKeyFactory", row).of("SecretKeyFactory"))
        assertEquals(fallback, engineTypes.of("SecretKeyFactory"))
    }
}
