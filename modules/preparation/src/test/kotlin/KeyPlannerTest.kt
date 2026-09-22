package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.key.plan.KeyPlanner
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyRecipe
import io.github.junekim0007.cryptobench.preparation.engine.EngineTypes
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.port.Availability
import io.github.junekim0007.cryptobench.preparation.port.DeviceCapability
import org.junit.Assert.assertEquals
import org.junit.Test

class KeyPlannerTest {

    private val device = object : DeviceCapability {
        private val serves = mapOf(
            "AndroidOpenSSL" to setOf("KeyGenerator/AES", "KeyGenerator/HmacSHA256", "KeyGenerator/ChaCha20", "KeyPairGenerator/RSA", "KeyPairGenerator/EC"),
            "BC" to setOf("KeyPairGenerator/RSA"),
            "Vault" to emptySet(),
        )

        override fun providers(): List<String> = listOf("AndroidOpenSSL", "BC", "Vault")

        override fun check(provider: String, type: String, algorithm: String): Availability =
            if ("$type/$algorithm" in serves[provider].orEmpty()) Availability.Available else Availability.Unavailable("not_registered")
    }

    private val planner = KeyPlanner(device)

    private fun plan(type: String, algorithm: String, provider: String = "AndroidOpenSSL", keySize: Int? = null) =
        planner.plan(BenchmarkCase(type, algorithm, provider, EngineTypes.standard().operationsOf(type).first(), keySize = keySize, inputSize = 1024))

    /** Cipher does not say whether its key is secret or a pair; the device's generators do. */
    @Test
    fun theDeviceDecidesTheCipherKey() {
        assertEquals(KeyRecipe.Secret("AES", 256, "AndroidOpenSSL"), plan("Cipher", "AES/GCM/NoPadding", keySize = 256))
        assertEquals(KeyRecipe.Pair("RSA", 2048, "AndroidOpenSSL"), plan("Cipher", "RSA/ECB/OAEPPadding", keySize = 2048))
    }

    @Test
    fun eachTypeGetsItsShape() {
        assertEquals(KeyRecipe.None, plan("MessageDigest", "SHA-256"))
        assertEquals(KeyRecipe.Secret("HmacSHA256", null, "AndroidOpenSSL"), plan("Mac", "HmacSHA256"))
        assertEquals(KeyRecipe.Pair("EC", 256, "AndroidOpenSSL"), plan("Signature", "SHA256withECDSA", keySize = 256))
        assertEquals(KeyRecipe.Pair("EC", 256, "AndroidOpenSSL", count = 2), plan("KeyAgreement", "ECDH", keySize = 256))
    }

    /** A key from another provider is recorded as such, so a cross-provider pairing is visible, not silent. */
    @Test
    fun theCasesProviderGeneratesWhenItCanOtherwisePrecedenceDecides() {
        assertEquals(KeyRecipe.Pair("RSA", 2048, "BC"), plan("Signature", "SHA256withRSA", provider = "BC", keySize = 2048))
        assertEquals(KeyRecipe.Secret("AES", 128, "AndroidOpenSSL"), plan("Cipher", "AES/CBC/PKCS5Padding", provider = "Vault", keySize = 128))
    }

    /** ChaCha20-Poly1305 has no generator of its own; its key comes from ChaCha20's. */
    @Test
    fun aCipherFamilyGeneratorIsUsedWhenTheNameHasNone() {
        assertEquals(KeyRecipe.Secret("ChaCha20", 256, "AndroidOpenSSL"), plan("Cipher", "ChaCha20-Poly1305", keySize = 256))
    }

    @Test
    fun noGeneratorIsAnUnavailableRecipe() {
        assertEquals(KeyRecipe.Unavailable("no_key_generator: Serpent"), plan("Cipher", "Serpent/CBC/NoPadding"))
        assertEquals(KeyRecipe.Unavailable("no_key_generator: KeyGenerator.HmacSHA512"), plan("Mac", "HmacSHA512"))
    }

    /** The key a case needs comes from its operation, so a type nobody registered needs none once it is measured by a generator. */
    @Test
    fun theOperationDecidesWhetherAKeyIsNeeded() {
        assertEquals(KeyRecipe.None, planner.plan(BenchmarkCase("SecretKeyFactory", "PBKDF2WithHmacSHA256", "AndroidOpenSSL", Operation.GENERATE_KEY)))
        assertEquals(KeyRecipe.None, plan("MessageDigest", "SHA-256"))
    }

    /** A size written into the name is the key's size: AES_128 takes a 128-bit AES key, not the provider default. */
    @Test
    fun aSizeInTheNameBecomesTheKeySize() {
        assertEquals(KeyRecipe.Secret("AES", 128, "AndroidOpenSSL"), plan("Cipher", "AES_128/GCM/NoPadding"))
        assertEquals(KeyRecipe.Secret("AES", 256, "AndroidOpenSSL"), plan("Cipher", "AES_128/GCM/NoPadding", keySize = 256))
    }
}
