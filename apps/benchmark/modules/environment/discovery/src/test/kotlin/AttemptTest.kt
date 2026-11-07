package io.github.junekim0007.cryptobench.discovery

import io.github.junekim0007.cryptobench.discovery.trial.call.DefaultKeys
import io.github.junekim0007.cryptobench.discovery.trial.requirement.FactSheet
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test
import java.security.Provider
import java.security.SecureRandom
import java.security.Security
import java.security.spec.AlgorithmParameterSpec
import javax.crypto.KeyGeneratorSpi
import javax.crypto.SecretKey

/** Every probe level catches the same set: a LinkageError is the attempt's result, an OutOfMemoryError ends the probe. */
class AttemptTest {

    @Test
    fun aLinkageErrorIsRecordedUnderItsFact() {
        val sheet = FactSheet()
        sheet.measure("linked") { throw NoClassDefFoundError("org/missing/Helper") }
        sheet.measure("next") { "ran" }
        assertEquals(mapOf("linked" to mapOf("error" to "NoClassDefFoundError: org/missing/Helper"), "next" to "ran"), sheet.facts)
    }

    @Test
    fun anOutOfMemoryErrorEscapesEveryLevel() {
        assertThrows(OutOfMemoryError::class.java) { FactSheet().measure("fact") { throw OutOfMemoryError("heap") } }
        Security.addProvider(Exhausting())
        try {
            val keys = DefaultKeys(listOf(Security.getProvider("Exhausting")))
            assertThrows(OutOfMemoryError::class.java) { keys.secret(Security.getProvider("Exhausting"), "EXHAUST", null) }
        } finally {
            Security.removeProvider("Exhausting")
        }
    }

    @Test
    fun aKeyGeneratorsLinkageErrorIsARefusedKey() {
        Security.addProvider(Exhausting())
        try {
            val keys = DefaultKeys(listOf(Security.getProvider("Exhausting")))
            assertThrows(NoClassDefFoundError::class.java) { keys.secret(Security.getProvider("Exhausting"), "UNLINKED", null) }
            assertEquals(1, keys.stats().refused)
        } finally {
            Security.removeProvider("Exhausting")
        }
    }

    @Suppress("DEPRECATION")
    private class Exhausting : Provider("Exhausting", 1.0, "a generator out of memory, one missing a class") {
        init {
            put("KeyGenerator.EXHAUST", OutOfMemory::class.java.name)
            put("KeyGenerator.UNLINKED", Unlinked::class.java.name)
        }
    }

    open class Throwing(private val thrown: () -> Throwable) : KeyGeneratorSpi() {
        override fun engineInit(random: SecureRandom?) = Unit
        override fun engineInit(params: AlgorithmParameterSpec?, random: SecureRandom?) = Unit
        override fun engineInit(keysize: Int, random: SecureRandom?) = Unit
        override fun engineGenerateKey(): SecretKey = throw thrown()
    }

    class OutOfMemory : Throwing({ OutOfMemoryError("heap") })

    class Unlinked : Throwing({ NoClassDefFoundError("org/missing/Helper") })
}
