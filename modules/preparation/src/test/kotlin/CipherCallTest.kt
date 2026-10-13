package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.operation.CipherCall
import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertFalse
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

    @Test
    fun aRepeatableInitRunsOnceAndTheExactResultMatchesAPlainDoFinal() {
        val iv = IvParameterSpec(ByteArray(16))
        val cipher = Cipher.getInstance("AES/CBC/PKCS5Padding")
        val call = CipherCall(cipher, message, { cipher.init(Cipher.ENCRYPT_MODE, key, iv) }, perCallParameters = false)
        assertFalse(call.reinitialises)
        val plain = Cipher.getInstance("AES/CBC/PKCS5Padding").apply { init(Cipher.ENCRYPT_MODE, key, iv) }.doFinal(message)
        assertArrayEquals(plain, call.invocation().once() as ByteArray)
    }

    @Test
    fun aProviderThatRefusesARepeatIsDetectedAndReinitialised() {
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        var nonces = 0
        val call = CipherCall(cipher, message, { cipher.init(Cipher.ENCRYPT_MODE, key, GCMParameterSpec(128, ByteArray(12) { (nonces + it).toByte() }.also { nonces++ })) }, perCallParameters = false)
        assertTrue(call.reinitialises)
        repeat(3) { call.invocation().perIteration() }
    }

    @Test
    fun oneFixedNonceIsRefusedWithAReason() {
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        val failure = assertThrows(IllegalArgumentException::class.java) {
            CipherCall(cipher, message, { cipher.init(Cipher.ENCRYPT_MODE, key, GCMParameterSpec(128, ByteArray(12))) }, perCallParameters = false)
        }
        assertTrue(failure.message!!.startsWith("not_repeatable:"))
    }

    @Test
    fun perCallParametersAlwaysReinitialise() {
        val cipher = Cipher.getInstance("AES/CBC/PKCS5Padding")
        val call = CipherCall(cipher, message, { n -> cipher.init(Cipher.ENCRYPT_MODE, key, IvParameterSpec(ByteArray(16) { n.toByte() })) }, perCallParameters = true)
        assertTrue(call.reinitialises)
    }
}
