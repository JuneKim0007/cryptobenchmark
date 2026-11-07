package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterialGenerator
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyRecipe
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test
import java.security.interfaces.ECPublicKey
import java.security.interfaces.RSAPublicKey

class KeyMaterialGeneratorTest {

    private val generator = KeyMaterialGenerator()

    @Test
    fun secretKeysHaveTheRequestedSize() {
        val material = generator.generate(KeyRecipe.Secret("AES", 128, "SunJCE")) as KeyMaterial.Secret
        assertEquals(16, material.key.encoded.size)
    }

    @Test
    fun pairsHaveTheRequestedSize() {
        val rsa = generator.generate(KeyRecipe.Pair("RSA", 2048, "SunRsaSign")) as KeyMaterial.Pairs
        assertEquals(2048, (rsa.pairs.single().public as RSAPublicKey).modulus.bitLength())
        val agreement = generator.generate(KeyRecipe.Pair("EC", 256, "SunEC", count = 2)) as KeyMaterial.Pairs
        assertEquals(2, agreement.pairs.size)
        assertEquals(256, (agreement.pairs.first().public as ECPublicKey).params.curve.field.fieldSize)
    }

    @Test
    fun anUnavailableRecipeIsRefused() {
        val error = assertThrows(IllegalArgumentException::class.java) {
            generator.generate(KeyRecipe.Unavailable("no_key_generator: ChaCha20"))
        }
        assertEquals("unavailable_recipe: no_key_generator: ChaCha20", error.message)
    }

    /** A key spec from the config replaces the size: a named curve, an RSA exponent. */
    @Test
    fun aBoundKeySpecDrivesGeneration() {
        val curve = mapOf("class" to "java.security.spec.ECGenParameterSpec", "arguments" to listOf("secp256r1"))
        val ec = generator.generate(KeyRecipe.Pair("EC", null, "SunEC", parameters = curve)) as KeyMaterial.Pairs
        assertEquals(256, (ec.pairs.single().public as ECPublicKey).params.curve.field.fieldSize)
        val exponent = mapOf("class" to "java.security.spec.RSAKeyGenParameterSpec", "arguments" to listOf(2048, 3))
        val rsa = generator.generate(KeyRecipe.Pair("RSA", null, "SunRsaSign", parameters = exponent)) as KeyMaterial.Pairs
        assertEquals(java.math.BigInteger.valueOf(3), (rsa.pairs.single().public as RSAPublicKey).publicExponent)
    }
}
