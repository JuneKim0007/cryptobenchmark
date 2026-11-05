package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.parameter.resolve.KeyFields
import io.github.junekim0007.cryptobench.preparation.parameter.resolve.ResolvedParameters
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import java.math.BigInteger
import java.security.KeyPairGenerator
import java.security.Signature
import java.security.interfaces.ECPublicKey
import java.security.spec.ECGenParameterSpec
import java.security.spec.ECParameterSpec
import java.security.spec.MGF1ParameterSpec
import java.security.spec.PSSParameterSpec
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.IvParameterSpec
import javax.crypto.spec.OAEPParameterSpec
import javax.crypto.spec.PSource

/** What the provider used, read back per parameter kind after one call. */
class ResolvedParametersTest {

    private fun aes(bits: Int) = KeyMaterial.Secret(KeyGenerator.getInstance("AES", "SunJCE").apply { init(bits) }.generateKey())

    private fun pairs(algorithm: String, init: KeyPairGenerator.() -> Unit) =
        KeyMaterial.Pairs(listOf(KeyPairGenerator.getInstance(algorithm).apply(init).generateKeyPair()))

    private fun encrypted(transformation: String, key: KeyMaterial, spec: java.security.spec.AlgorithmParameterSpec? = null): Cipher {
        val cipher = Cipher.getInstance(transformation, "SunJCE")
        val encrypting = key.secretKeyOrNull ?: key.keyPairsOrNull!!.first().public
        if (spec == null) cipher.init(Cipher.ENCRYPT_MODE, encrypting) else cipher.init(Cipher.ENCRYPT_MODE, encrypting, spec)
        cipher.doFinal(ByteArray(32))
        return cipher
    }

    @Test
    fun gcmReportsItsIvLengthAndTagBits() {
        val key = aes(128)
        val cipher = encrypted("AES/GCM/NoPadding", key, GCMParameterSpec(96, ByteArray(12) { it.toByte() }))
        assertEquals(
            linkedMapOf<String, Any>("mode" to "GCM", "padding" to "NoPadding", "ivBytes" to 12, "tagBits" to 96, "keyBits" to 128),
            ResolvedParameters.of(cipher, key, null),
        )
    }

    @Test
    fun cbcReportsTheIvItChoseAndOneItWasGiven() {
        val key = aes(256)
        val chosen = ResolvedParameters.of(encrypted("AES/CBC/PKCS5Padding", key), key, null)
        assertEquals(linkedMapOf<String, Any>("mode" to "CBC", "padding" to "PKCS5Padding", "ivBytes" to 16, "keyBits" to 256), chosen)
        val given = ResolvedParameters.of(encrypted("AES/CBC/PKCS5Padding", key, IvParameterSpec(ByteArray(16))), key, null)
        assertEquals(16, given["ivBytes"])
    }

    @Test
    fun aKeyWrapIntegrityCheckValueIsNotAnIv() {
        val key = aes(128)
        val wrap = ResolvedParameters.of(encrypted("AES/KWP/NoPadding", key), key, null)
        assertEquals("KWP", wrap["mode"])
        assertFalse(wrap.toString(), "ivBytes" in wrap)
    }

    @Test
    fun oaepReportsDigestMgf1AndLabelLength() {
        val rsa = pairs("RSA") { initialize(2048) }
        val spec = OAEPParameterSpec("SHA-256", "MGF1", MGF1ParameterSpec.SHA1, PSource.PSpecified(ByteArray(5)))
        val cipher = encrypted("RSA/ECB/OAEPPadding", rsa, spec)
        assertEquals(
            linkedMapOf<String, Any>("mode" to "ECB", "padding" to "OAEPPadding", "digest" to "SHA-256", "mgf1" to "SHA-1", "labelBytes" to 5, "keyBits" to 2048),
            ResolvedParameters.of(cipher, rsa, null),
        )
    }

    @Test
    fun oaepDefaultsAreWhatTheProviderFilledIn() {
        val rsa = pairs("RSA") { initialize(2048) }
        val resolved = ResolvedParameters.of(encrypted("RSA/ECB/OAEPWithSHA-256AndMGF1Padding", rsa), rsa, null)
        assertEquals("SHA-256", resolved["digest"])
        assertEquals("SHA-1", resolved["mgf1"])
        assertEquals(0, resolved["labelBytes"])
    }

    @Test
    fun pssSignatureReportsDigestAndMgf1() {
        val rsa = pairs("RSASSA-PSS") { initialize(2048) }
        val signature = Signature.getInstance("RSASSA-PSS").apply {
            setParameter(PSSParameterSpec("SHA-256", "MGF1", MGF1ParameterSpec.SHA256, 32, 1))
            initSign(rsa.pairs.first().private)
            update(ByteArray(8))
            sign()
        }
        assertEquals(
            linkedMapOf<String, Any>("digest" to "SHA-256", "mgf1" to "SHA-256", "keyBits" to 2048),
            ResolvedParameters.of(signature, rsa, null),
        )
    }

    @Test
    fun anEcKeyReportsItsCurveAndFieldSize() {
        val ec = pairs("EC") { initialize(ECGenParameterSpec("secp384r1")) }
        val signature = Signature.getInstance("SHA256withECDSA").apply { initSign(ec.pairs.first().private) }
        val resolved = ResolvedParameters.of(signature, ec, null)
        assertEquals(384, resolved["keyBits"])
        // Older JDKs name the curve by OID, newer ones by its standard name.
        assertTrue(resolved.toString(), resolved["curve"] in setOf("secp384r1", "1.3.132.0.34"))
    }

    @Test
    fun anUnnamedCurveGetsItsFieldSizeAndAStableHash() {
        val named = (pairs("EC") { initialize(ECGenParameterSpec("secp256r1")) }.pairs.first().public as ECPublicKey).params
        val unnamed = ECParameterSpec(named.curve, named.generator, named.order, named.cofactor)
        val tweaked = ECParameterSpec(named.curve, named.generator, named.order.subtract(BigInteger.ONE), named.cofactor)
        val curve = KeyFields.curve(unnamed, "NoSuchCurveAlgorithm")
        assertTrue(curve, curve.matches(Regex("field256-[0-9a-f]{8}")))
        assertEquals(curve, KeyFields.curve(unnamed, "NoSuchCurveAlgorithm"))
        assertFalse(curve == KeyFields.curve(tweaked, "NoSuchCurveAlgorithm"))
    }

    @Test
    fun aGeneratedKeyIsSizedFromTheResultNotThePreparedMaterial() {
        val generated = KeyGenerator.getInstance("AES").apply { init(192) }.generateKey()
        assertEquals(linkedMapOf<String, Any>("keyBits" to 192), ResolvedParameters.of(null, KeyMaterial.None, generated))
        val pair = KeyPairGenerator.getInstance("RSA").apply { initialize(3072) }.generateKeyPair()
        assertEquals(linkedMapOf<String, Any>("keyBits" to 3072), ResolvedParameters.of(null, KeyMaterial.None, pair))
    }
}
