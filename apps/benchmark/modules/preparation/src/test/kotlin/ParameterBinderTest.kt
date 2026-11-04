package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.parameter.bind.BindException
import io.github.junekim0007.cryptobench.preparation.parameter.bind.ParameterBinder
import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertTrue
import org.junit.Assert.assertThrows
import org.junit.Test
import org.yaml.snakeyaml.Yaml
import java.io.File
import java.security.KeyPairGenerator
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.OAEPParameterSpec

class ParameterBinderTest {

    private val binder = ParameterBinder()

    private fun tree(yaml: String): Map<String, Any> = Yaml().load(yaml)

    private fun failure(yaml: String): String? =
        assertThrows(BindException::class.java) { binder.bind(tree(yaml), "parameters") }.message

    @Test
    fun nestedObjectsAndStaticFieldsBuildAnOaepSpec() {
        val bound = binder.bind(tree("""
            class: javax.crypto.spec.OAEPParameterSpec
            arguments:
            - SHA-256
            - MGF1
            - {field: java.security.spec.MGF1ParameterSpec.SHA256}
            - {field: javax.crypto.spec.PSource${'$'}PSpecified.DEFAULT}
        """.trimIndent()), "parameters")
        val spec = bound.next() as OAEPParameterSpec
        assertEquals("SHA-256", spec.digestAlgorithm)
        val rsa = KeyPairGenerator.getInstance("RSA").apply { initialize(2048) }.generateKeyPair()
        Cipher.getInstance("RSA/ECB/OAEPPadding", "SunJCE").init(Cipher.ENCRYPT_MODE, rsa.public, spec)
        assertFalse(bound.varies)
    }

    /** GCM refuses a repeated IV, so fresh(n) must give new bytes on every next(). */
    @Test
    fun freshBytesDifferOnEveryCall() {
        val bound = binder.bind(tree("{class: javax.crypto.spec.GCMParameterSpec, arguments: [128, fresh(12)]}"), "parameters")
        val first = bound.next() as GCMParameterSpec
        val second = bound.next() as GCMParameterSpec
        assertTrue(bound.varies)
        assertEquals(12, first.iv.size)
        assertNotEquals(first.iv.toList(), second.iv.toList())
        val key = KeyGenerator.getInstance("AES").generateKey()
        val cipher = Cipher.getInstance("AES/GCM/NoPadding", "SunJCE")
        cipher.init(Cipher.ENCRYPT_MODE, key, first); cipher.doFinal(ByteArray(16))
        cipher.init(Cipher.ENCRYPT_MODE, key, second); cipher.doFinal(ByteArray(16))
    }

    @Test
    fun yamlValuesAreConvertedToWhatTheConstructorTakes() {
        val iv = binder.bind(tree("{class: javax.crypto.spec.IvParameterSpec, arguments: [!!binary AAECAwQFBgcICQoLDA0ODw==]}"), "parameters").next()
        assertArrayEquals(ByteArray(16) { it.toByte() }, (iv as javax.crypto.spec.IvParameterSpec).iv)
        val listIv = binder.bind(tree("{class: javax.crypto.spec.IvParameterSpec, arguments: [[0, 1, 255]]}"), "parameters").next()
        assertArrayEquals(byteArrayOf(0, 1, -1), (listIv as javax.crypto.spec.IvParameterSpec).iv)
        val rsa = binder.bind(tree("{class: java.security.spec.RSAKeyGenParameterSpec, arguments: [2048, 65537]}"), "key").next()
        assertEquals(java.math.BigInteger.valueOf(65537), (rsa as java.security.spec.RSAKeyGenParameterSpec).publicExponent)
    }

    @Test
    fun namesEveryConstructorThatDidNotFit() {
        assertEquals(
            "bind_failed: parameters: no constructor of javax.crypto.spec.GCMParameterSpec takes [Integer 96, String x] -> [(int, byte[]) type mismatch]",
            failure("{class: javax.crypto.spec.GCMParameterSpec, arguments: [96, x]}"),
        )
    }

    @Test
    fun pointsAtThePathThatFailed() {
        assertEquals(
            "bind_failed: parameters.arguments[2]: no public field java.security.spec.MGF1ParameterSpec.SHA999",
            failure("{class: javax.crypto.spec.OAEPParameterSpec, arguments: [SHA-256, MGF1, {field: java.security.spec.MGF1ParameterSpec.SHA999}, {field: javax.crypto.spec.PSource${'$'}PSpecified.DEFAULT}]}"),
        )
        assertEquals("bind_failed: parameters: no class javax.crypto.spec.NoSuchSpec on this runtime", failure("{class: javax.crypto.spec.NoSuchSpec}"))
        assertEquals("bind_failed: parameters: unknown keys [args]", failure("{class: javax.crypto.spec.IvParameterSpec, args: [1]}"))
    }

    /** The file is user-edited and binding runs constructors: only parameter-spec types may be named. */
    @Test
    fun refusesClassesOutsideThePolicyBeforeRunningThem() {
        val target = File.createTempFile("bind", ".txt").also { it.delete() }
        val message = failure("{class: java.io.FileOutputStream, arguments: ['${target.absolutePath}']}")
        assertTrue(message!!, message.contains("java.io.FileOutputStream is not allowed"))
        assertFalse("a refused constructor ran", target.exists())
    }

    @Test
    fun theRootMustBeAParameterSpec() {
        assertEquals("bind_failed: parameters: java.math.BigInteger is not an AlgorithmParameterSpec", failure("{class: java.math.BigInteger, arguments: ['7']}"))
    }
}
