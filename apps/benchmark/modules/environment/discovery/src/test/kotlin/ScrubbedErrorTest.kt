package io.github.junekim0007.cryptobench.discovery

import io.github.junekim0007.cryptobench.discovery.adapter.ProviderProbe
import io.github.junekim0007.cryptobench.jca.failure.ErrorText
import io.github.junekim0007.cryptobench.discovery.trial.DefaultRunTrial
import io.github.junekim0007.cryptobench.discovery.trial.TrialRunner
import io.github.junekim0007.cryptobench.discovery.trial.call.DefaultKeys
import io.github.junekim0007.cryptobench.discovery.trial.requirement.RequirementTrial
import io.github.junekim0007.cryptobench.discovery.trial.requirement.Sweep
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.security.NoSuchAlgorithmException
import java.security.Provider
import java.security.Security

/** A provider message that prints a key reaches the files, and the classify model, only scrubbed and capped, at every level. */
class ScrubbedErrorTest {

    @Test
    fun aKeyBearingMessageIsScrubbedAndCappedAtEveryLevel() {
        val providers = Security.getProviders() + Leaky()
        val capture = ProviderProbe().capture(providers)
        val keys = DefaultKeys(providers.toList())
        val trial = DefaultRunTrial().run(TrialRunner().run(capture, providers), providers, keys)
        val requirements = RequirementTrial().run(capture, trial, providers, keys)
        val leaky = trial.services.filter { it.provider == "Leaky" }
        val levels = mapOf(
            "level 1" to leaky.single { it.algorithm == "UNMADE" }.outcome.error,
            "level 2" to leaky.single { it.algorithm == "AES/CBC/NoPadding" }.defaultRun!!.error,
            "level 3" to requirements.services.single { it.provider == "Leaky" && it.algorithm == "AES/CBC/NoPadding" }.detail,
        )
        levels.forEach { (level, text) ->
            assertTrue("$level: $text", text.isNotEmpty() && text.length <= ErrorText.CAP)
            assertTrue("$level key left in: $text", SECRET !in text && "<removed>" in text)
        }
    }

    @Test
    fun everyCommonKeyEncodingIsRemoved() {
        ENCODINGS.forEach { (name, encoding) ->
            assertEquals(name, "InvalidKeyException: key=<removed> for this cipher", ErrorText.clean("InvalidKeyException: key=$encoding for this cipher"))
        }
    }

    @Test
    fun anOrdinaryProviderMessageIsLeftAsItIs() {
        ORDINARY.forEach { assertEquals(it, ErrorText.clean(it)) }
    }

    @Test
    fun aUrlInAProviderMessageIsKeptAndAKeyBesideItRemoved() {
        URLS.forEach { assertEquals(it, "NoSuchAlgorithmException: Please see $it", ErrorText.clean("NoSuchAlgorithmException: Please see $it")) }
        val base64 = ENCODINGS.getValue("base64 of 256 bits")
        assertEquals("see https://keys.example/get?k=<removed>", ErrorText.clean("see https://keys.example/get?k=$base64"))
        assertEquals("see https://keys.<removed>", ErrorText.clean("see https://keys.example/$base64"))
        assertEquals("see https://keys.example/a modulus=<removed>", ErrorText.clean("see https://keys.example/a modulus=${ENCODINGS.getValue("RSA modulus")}"))
    }

    @Test
    fun aPrefixedRefusalStaysWithinTheCap() {
        val long = IllegalStateException("provider detail ".repeat(40))
        assertTrue(ErrorText.of(long, "generation refused: ").length <= ErrorText.CAP)
        val firstRefusal = Sweep.of(listOf(123456)) { throw long }.getValue("firstRefusal").toString()
        assertTrue(firstRefusal, firstRefusal.startsWith("123456: ") && firstRefusal.length <= ErrorText.CAP)
    }

    @Suppress("DEPRECATION")
    private class Leaky : Provider("Leaky", 1.0, "prints its key in every refusal") {
        init {
            put("Cipher.AES/CBC/NoPadding", LeakingCipher::class.java.name)
            putService(Unmade(this))
        }
    }

    private class Unmade(provider: Provider) : Provider.Service(provider, "Cipher", "UNMADE", "no.Class", null, null) {
        override fun newInstance(constructorParameter: Any?): Any = throw NoSuchAlgorithmException(MESSAGE)
    }

    class LeakingCipher : RequirementTrialTest.RefusingCipher() {
        override fun refusal(): Exception = IllegalStateException(MESSAGE)
    }

    private companion object {
        const val SECRET = "00112233445566778899aabbccddeeff00112233445566778899aabbccddeeff"
        val MESSAGE = "key=$SECRET " + "provider detail ".repeat(40)

        val ENCODINGS = mapOf(
            "base64 of 128 bits" to "/quQaw7NZg9PtZvKiodfkg==",
            "base64 of 256 bits" to "qtwVmawCNcS+RV1AAy+UZtiv2/VWk+NXLPOrNdO8Eao=",
            "base64url" to "9LT5_F_ilSBb_ptd0zfytsQJjmF7Ou8wtcMytxTn7-o",
            "hex of 128 bits" to "feab906b0ecd660f4fb59bca8a875f92",
            "hex of 64 bits" to "932210a5754022dd",
            "hex with spaces" to "fe ab 90 6b 0e cd 66 0f 4f b5 9b ca 8a 87 5f 92",
            "hex with dashes" to "FE-AB-90-6B-0E-CD-66-0F-4F-B5-9B-CA-8A-87-5F-92",
            "hex with colons" to "fe:ab:90:6b:0e:cd:66:0f:4f:b5:9b:ca:8a:87:5f:92",
            "0x list" to "0xfe, 0xab, 0x90, 0x6b, 0x0e, 0xcd, 0x66, 0x0f, 0x4f, 0xb5, 0x9b, 0xca",
            "unsigned bytes" to "[254, 171, 144, 107, 14, 205, 102, 15, 79, 181, 155, 202, 138, 135, 95, 146]",
            "signed bytes" to "[-2, -85, -112, 107, 14, -51, 102, 15, 79, -75, -101, -54, -118, -121, 95, -110]",
            "hex wrapped every 16" to "feab906b0ecd660f\n4fb59bca8a875f92\nd33b046f",
            "wrapped base64 and its short last line" to
                "4tW8CmPXA/JY4/JlHoY1ahlc7xLJBX3um9rTC8xLXrwP1wlzm/5esUH83xj35S+g\nhJtDcl6ZE53u2hml9NCcXwhUSiQpyCuIYGN8MvkkRBjnjhOr1XLYm+Np17vEXOUH\nEraR/g==",
            "RSA modulus" to "2519590847565789349402718324004839857142928212620403202777713783604366202070759555626401852588078440691829064124951508218929855914917618450280848912007284499268739280728777673597141834727026189637501497182469116507761337985909570009733045974880842840179742910064245869181719511874612151517265463228221686998754918242243363725908514186546204357679842338718477444792073993423658482382428119816381501067481045166037730605620161967625613384414360383390441495263443219011465754445417842402092461651572335077870774981712577246796292638635637328991215483143816789988504044536402352738195137863656439121201039712282120720357",
        )

        // URLs the token pass cut before the URL guard, from real runs.
        val URLS = listOf(
            "https://android-developers.googleblog.com/2018/03/cryptography-changes-in-android-p.html",
            "http://www.w3.org/2001/10/xml-exc-c14n#WithComments",
            "http://www.w3.org/TR/2001/REC-xml-c14n-20010315",
            "http://www.w3.org/2006/12/xml-c14n11",
            "https://android.googlesource.com/platform/libcore/+/refs/tags/android-9.0.0_r1/ojluni/src/main/java/sun/security/jca/Providers.java",
            "https://csrc.nist.gov/pubs/sp/800/67/r2/final",
            "https://csrc.nist.gov/pubs/sp/800/38/d/final",
            "https://datatracker.ietf.org/doc/html/draft-connolly-cfrg-xwing-kem-11",
            "https://github.com/bcgit/bc-java/blob/main/prov/src/main/java/org/bouncycastle/jcajce/provider/symmetric/AES.java",
        )

        val ORDINARY = listOf(
            "NoSuchAlgorithmException: no such algorithm: PBEWithHmacSHA256AndAES_256 for provider BC",
            "NoSuchAlgorithmException: Cannot find any provider supporting RSA/ECB/OAEPWithSHA-256AndMGF1Padding",
            "InvalidKeyException: Illegal key size or default parameters",
            "InvalidAlgorithmParameterException: Wrong IV length: must be 16 bytes long",
            "InvalidAlgorithmParameterException: Unsupported tag length: 32, must be one of 96, 104, 112, 120, 128",
            "InvalidKeySpecException: Key length is 1024 bits, expected 2048",
            "ProviderException: Error code 0x80000001 in org.bouncycastle.jcajce.provider.symmetric.util.BaseBlockCipher",
            "SignatureException: Signature length not correct: got 255 but was expecting 256",
            "InvalidKeyException: No installed provider supports this key: javax.crypto.spec.SecretKeySpec",
            "NoSuchAlgorithmException: SLH-DSA-SHA2-128s KeyPairGenerator not available",
            "UnsupportedOperationException: engineGetOutputSize not supported for SHA3-256withECDSAinP1363Format",
            "KeyStoreException: AndroidKeyStoreBCWorkaround cannot import ChaCha20-Poly1305 keys",
            "BadPaddingException: pad block corrupted, offset 0x1f, count 24",
            "NoSuchAlgorithmException: 2.16.840.1.101.3.4.1.46 not found for Cipher_1-2-804-2-1-1-1-1-1-3-8-1_ENCRYPT_BC",
            "ShortBufferException: Output buffer too short: 15 bytes given, 32 bytes needed",
            "InvalidParameterSpecException: no spec for GOST3411-2012-256 with PBKDF2WithHmacSHA256",
            "IllegalArgumentException: DSTU7624-128/CCM requires nonce of 16, 32 or 64 bytes",
            "IllegalStateException: RequirementTrialTest\$UnencodedFactory\$engineGenerateSecret\$1 no encoding",
            "IllegalStateException: TlsMasterSecretGenerator must be initialized",
            "InvalidKeyException: Key length not 128/192/256 bits.",
            "SignatureException: SignatureSpi\$Falcon512_ECDSA_brainpoolP256r1_SHA256 and secp256r1 refused",
            "ProviderException: AES/GCM/NoPadding at com.android.org.conscrypt.OpenSSLCipher\$EVP_AEAD\$AES\$GCM.engineDoFinal",
        )
    }
}
