package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.operation.CipherCall
import io.github.junekim0007.cryptobench.preparation.operation.PerCall
import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.IvParameterSpec

class CipherCallTest {

    private val key = KeyGenerator.getInstance("AES").apply { init(128) }.generateKey()
    private val message = ByteArray(100) { it.toByte() }
    private val cbc = { Cipher.getInstance("AES/CBC/PKCS5Padding") }

    @Test
    fun initPerCallInitialisesEveryCallAndTheExactResultMatchesAPlainDoFinal() {
        val iv = IvParameterSpec(ByteArray(16))
        var inits = 0
        val call = CipherCall(cbc, message, { cipher, _ -> inits++; cipher.init(Cipher.ENCRYPT_MODE, key, iv) })
        val invocation = call.invocation(PerCall.INIT_AND_OPERATION)
        val before = inits
        repeat(3) { invocation.perIteration() }
        assertEquals(before + 3, inits)
        val plain = cbc().apply { init(Cipher.ENCRYPT_MODE, key, iv) }.doFinal(message)
        assertArrayEquals(plain, invocation.once() as ByteArray)
    }

    @Test
    fun operationOnlyNeverInitsInsideTheCall() {
        var inits = 0
        val ecb = { Cipher.getInstance("AES/ECB/PKCS5Padding") }
        val invocation = CipherCall(ecb, message, { cipher, _ -> inits++; cipher.init(Cipher.ENCRYPT_MODE, key) }).invocation(PerCall.OPERATION)
        val before = inits
        repeat(3) { invocation.perIteration() }
        assertEquals(before, inits)
        assertArrayEquals(ecb().apply { init(Cipher.ENCRYPT_MODE, key) }.doFinal(message), invocation.once() as ByteArray)
    }

    @Test
    fun notFixedMakesTheInstanceEveryCall() {
        val made = mutableListOf<Cipher>()
        val invocation = CipherCall({ cbc().also { made += it } }, message, { cipher, n -> cipher.init(Cipher.ENCRYPT_MODE, key, IvParameterSpec(ByteArray(16) { n.toByte() })) })
            .invocation(PerCall.INSTANCE_INIT_AND_OPERATION)
        val before = made.size
        repeat(3) { invocation.perIteration() }
        assertEquals(before + 3, made.size)
        assertEquals(made.size, made.toSet().size)
    }

    @Test
    fun oneFixedNonceIsRefusedWithAReason() {
        val failure = assertThrows(IllegalArgumentException::class.java) {
            CipherCall({ Cipher.getInstance("AES/GCM/NoPadding") }, message, { cipher, _ -> cipher.init(Cipher.ENCRYPT_MODE, key, GCMParameterSpec(128, ByteArray(12))) })
                .invocation(PerCall.INIT_AND_OPERATION)
        }
        assertTrue(failure.message!!.startsWith("not_repeatable:"))
    }

    @Test
    fun eachCallTakesTheNextParameterIndex() {
        val seen = mutableListOf<Int>()
        val call = CipherCall(cbc, message, { cipher, n -> seen += n; cipher.init(Cipher.ENCRYPT_MODE, key, IvParameterSpec(ByteArray(16) { n.toByte() })) })
        call.invocation(PerCall.INIT_AND_OPERATION).perIteration()
        assertEquals(listOf(0, 1, 2), seen)
    }
}
