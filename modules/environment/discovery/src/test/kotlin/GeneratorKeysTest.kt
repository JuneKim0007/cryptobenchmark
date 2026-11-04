package io.github.junekim0007.cryptobench.discovery

import io.github.junekim0007.cryptobench.discovery.contract.ServiceTrialEntry
import io.github.junekim0007.cryptobench.discovery.contract.TrialOutcome
import io.github.junekim0007.cryptobench.discovery.contract.TrialReport
import io.github.junekim0007.cryptobench.discovery.contract.TriedKey
import io.github.junekim0007.cryptobench.discovery.trial.DefaultRunTrial
import org.junit.Assert.assertEquals
import org.junit.Test
import java.math.BigInteger
import java.security.InvalidParameterException
import java.security.KeyPair
import java.security.KeyPairGeneratorSpi
import java.security.PrivateKey
import java.security.Provider
import java.security.PublicKey
import java.security.SecureRandom
import java.security.interfaces.RSAKey
import java.security.spec.AlgorithmParameterSpec
import javax.crypto.KeyGeneratorSpi
import javax.crypto.SecretKey

/** A made-up provider: the key's encoding per size, and a pair whose private key stays inside. */
class GeneratorKeysTest {

    private fun run(type: String) = DefaultRunTrial().run(
        TrialReport(1L, listOf(ServiceTrialEntry("Sized", type, "X", TrialOutcome.SUCCESS))), arrayOf(SizedProvider()),
    ).services.single().defaultRun!!

    @Test
    fun everySizeIsRecordedWithItsOwnKeyAndARefusalAsOne() {
        val outcome = run("KeyGenerator")
        assertEquals("exportable" to "RAW", outcome.keyMaterial to outcome.keyFormat)
        assertEquals(listOf(TriedKey(128, "exportable", "RAW"), TriedKey(192, refused = true), TriedKey(256, "non_exportable")), outcome.triedKeys)
    }

    @Test
    fun aPairsPrivateKeyDecidesAndNoSizeAboveItsDefaultIsAsked() {
        val outcome = run("KeyPairGenerator")
        assertEquals("non_exportable" to "", outcome.keyMaterial to outcome.keyFormat)
        assertEquals(listOf(256, 384, 1024), outcome.triedKeys.map { it.size })
    }
}

class SizedSecret(private val bytes: ByteArray?) : SecretKey {
    override fun getAlgorithm() = "X"
    override fun getFormat() = bytes?.let { "RAW" }
    override fun getEncoded() = bytes
}

class SizedKeyGenerator : KeyGeneratorSpi() {
    private var bits = 64

    override fun engineInit(random: SecureRandom?) = Unit
    override fun engineInit(params: AlgorithmParameterSpec?, random: SecureRandom?) = Unit
    override fun engineInit(keysize: Int, random: SecureRandom?) {
        if (keysize == 192) throw InvalidParameterException("no such size")
        bits = keysize
    }

    override fun engineGenerateKey(): SecretKey = SizedSecret(if (bits == 256) null else ByteArray(bits / 8))
}

class HeldPrivate : PrivateKey {
    override fun getAlgorithm() = "X"
    override fun getFormat(): String? = null
    override fun getEncoded(): ByteArray? = null
}

class OpenPublic : PublicKey, RSAKey {
    override fun getModulus(): BigInteger = BigInteger.ONE.shiftLeft(2047)
    override fun getParams(): AlgorithmParameterSpec? = null
    override fun getAlgorithm() = "X"
    override fun getFormat() = "X.509"
    override fun getEncoded() = ByteArray(8)
}

class HeldPairGenerator : KeyPairGeneratorSpi() {
    override fun initialize(keysize: Int, random: SecureRandom?) = Unit
    override fun generateKeyPair() = KeyPair(OpenPublic(), HeldPrivate())
}

@Suppress("DEPRECATION")
class SizedProvider : Provider("Sized", 1.0, "test fixture") {
    init {
        put("KeyGenerator.X", SizedKeyGenerator::class.java.name)
        put("KeyPairGenerator.X", HeldPairGenerator::class.java.name)
    }
}
