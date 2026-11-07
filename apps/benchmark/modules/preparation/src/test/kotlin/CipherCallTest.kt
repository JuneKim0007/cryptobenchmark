package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.operation.CipherCall
import io.github.junekim0007.cryptobench.preparation.operation.PerCall
import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test
import java.security.AlgorithmParameters
import java.security.Key
import java.security.Provider
import java.security.SecureRandom
import java.security.spec.AlgorithmParameterSpec
import javax.crypto.Cipher
import javax.crypto.CipherSpi
import javax.crypto.KeyGenerator
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.IvParameterSpec

// A wrap cipher as BC and AndroidOpenSSL register it: getOutputSize is -1.
class UnsizedWrap : CipherSpi() {
    private val inner = Cipher.getInstance("AES/KW/NoPadding", "SunJCE")

    override fun engineSetMode(mode: String?) {}
    override fun engineSetPadding(padding: String?) {}
    override fun engineGetBlockSize(): Int = 8
    override fun engineGetOutputSize(inputLen: Int): Int = -1
    override fun engineGetIV(): ByteArray? = null
    override fun engineGetParameters(): AlgorithmParameters? = null
    override fun engineInit(opmode: Int, key: Key, random: SecureRandom?) = inner.init(opmode, key, random)
    override fun engineInit(opmode: Int, key: Key, params: AlgorithmParameterSpec?, random: SecureRandom?) = inner.init(opmode, key, params, random)
    override fun engineInit(opmode: Int, key: Key, params: AlgorithmParameters?, random: SecureRandom?) = inner.init(opmode, key, params, random)
    override fun engineUpdate(input: ByteArray?, offset: Int, length: Int): ByteArray? = inner.update(input, offset, length)
    override fun engineUpdate(input: ByteArray?, offset: Int, length: Int, output: ByteArray?, outputOffset: Int): Int =
        inner.update(input, offset, length, output, outputOffset)
    override fun engineDoFinal(input: ByteArray?, offset: Int, length: Int): ByteArray = inner.doFinal(input, offset, length)
    override fun engineDoFinal(input: ByteArray?, offset: Int, length: Int, output: ByteArray?, outputOffset: Int): Int =
        inner.doFinal(input, offset, length, output, outputOffset)
}

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

    @Test
    fun aWrapCipherWithNoSizeBoundRunsIntoABufferSizedBeforeTiming() {
        @Suppress("DEPRECATION")
        val wrapper = object : Provider("UnsizedWrap", 1.0, "getOutputSize -1") {
            init { put("Cipher.AESWrap", UnsizedWrap::class.java.name) }
        }
        val wrap = { Cipher.getInstance("AESWrap", wrapper) }
        val invocation = CipherCall(wrap, message.copyOf(96), { cipher, _ -> cipher.init(Cipher.ENCRYPT_MODE, key) }).invocation(PerCall.OPERATION)
        repeat(3) { invocation.perIteration() }
        val plain = Cipher.getInstance("AES/KW/NoPadding", "SunJCE").apply { init(Cipher.ENCRYPT_MODE, key) }.doFinal(message.copyOf(96))
        assertArrayEquals(plain, invocation.once() as ByteArray)
    }
}
