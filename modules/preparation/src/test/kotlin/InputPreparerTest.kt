package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.input.InputBytes
import io.github.junekim0007.cryptobench.preparation.input.InputPreparer
import io.github.junekim0007.cryptobench.preparation.input.OperationInput
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterialGenerator
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyRecipe
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.parameter.bind.ParameterBinder
import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertSame
import org.junit.Assert.assertTrue
import org.junit.Test
import java.security.Signature
import javax.crypto.Cipher

class InputPreparerTest {

    private val preparer = InputPreparer()
    private val keys = KeyMaterialGenerator()
    private val aes = keys.generate(KeyRecipe.Secret("AES", 128, "SunJCE"))
    private val rsa = keys.generate(KeyRecipe.Pair("RSA", 2048, "SunRsaSign"))
    private val ec = keys.generate(KeyRecipe.Pair("EC", 256, "SunEC"))

    private fun case(type: String, algorithm: String, provider: String, operation: Operation, inputSize: Int? = 64) =
        BenchmarkCase(type, algorithm, provider, operation, inputSize = inputSize, seed = 7)

    /** java.util.Random's algorithm is fixed by its specification, so a seed gives the same bytes on every runtime. */
    @Test
    fun messagesAreSeededAndASmallerSizeIsAPrefixOfALargerOne() {
        assertArrayEquals(InputBytes.of(7, 64), InputBytes.of(7, 64))
        assertArrayEquals(InputBytes.of(7, 64), InputBytes.of(7, 1024).copyOf(64))
        val message = preparer.prepare(case("MessageDigest", "SHA-256", "SUN", Operation.DIGEST), KeyMaterial.None, null) as OperationInput.Message
        assertArrayEquals(InputBytes.of(7, 64), message.bytes)
    }

    /** A GCM IV is drawn once for the ciphertext; decrypting must use that same spec, so it travels with the bytes. */
    @Test
    fun decryptGetsTheCiphertextAndTheSpecItWasMadeUnder() {
        val gcm = ParameterBinder().bind(mapOf("class" to "javax.crypto.spec.GCMParameterSpec", "arguments" to listOf(128, "fresh(12)")), "parameters")
        val input = preparer.prepare(case("Cipher", "AES/GCM/NoPadding", "SunJCE", Operation.DECRYPT), aes, gcm) as OperationInput.Ciphertext
        assertNotNull(input.spec)
        val cipher = Cipher.getInstance("AES/GCM/NoPadding", "SunJCE").apply { init(Cipher.DECRYPT_MODE, (aes as KeyMaterial.Secret).key, input.spec) }
        assertArrayEquals(InputBytes.of(7, 64), cipher.doFinal(input.bytes))
    }

    /** No spec given: the provider picked the IV, and those parameters are what decrypt needs. */
    @Test
    fun decryptWithoutASpecCarriesTheProvidersParameters() {
        val input = preparer.prepare(case("Cipher", "AES/CBC/PKCS5Padding", "SunJCE", Operation.DECRYPT), aes, null) as OperationInput.Ciphertext
        assertNull(input.spec)
        assertEquals(16, input.providerParameters!!.getParameterSpec(javax.crypto.spec.IvParameterSpec::class.java).iv.size)
    }

    @Test
    fun asymmetricDecryptEncryptsWithThePublicKey() {
        val input = preparer.prepare(case("Cipher", "RSA/ECB/OAEPPadding", "SunJCE", Operation.DECRYPT, inputSize = 32), rsa, null) as OperationInput.Ciphertext
        assertEquals(256, input.bytes.size)
        assertEquals(32, input.plaintextSize)
    }

    @Test
    fun verifyGetsAValidSignature() {
        val input = preparer.prepare(case("Signature", "SHA256withECDSA", "SunEC", Operation.VERIFY), ec, null) as OperationInput.SignedMessage
        val pair = (ec as KeyMaterial.Pairs).pairs.first()
        assertTrue(Signature.getInstance("SHA256withECDSA", "SunEC").apply { initVerify(pair.public); update(input.message) }.verify(input.signature))
    }

    @Test
    fun keyOperationsTakeNoInput() {
        assertSame(OperationInput.None, preparer.prepare(case("KeyPairGenerator", "RSA", "SunRsaSign", Operation.GENERATE_KEY_PAIR, inputSize = null), KeyMaterial.None, null))
    }
}
