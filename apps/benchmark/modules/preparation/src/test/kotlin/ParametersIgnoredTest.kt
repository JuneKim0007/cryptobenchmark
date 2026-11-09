import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.measurement.Phase
import io.github.junekim0007.cryptobench.preparation.operation.EncryptDefinition
import io.github.junekim0007.cryptobench.preparation.parameter.bind.ParameterBinder
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.security.AlgorithmParameters
import java.security.Key
import java.security.Provider
import java.security.SecureRandom
import java.security.Security
import java.security.spec.AlgorithmParameterSpec
import javax.crypto.Cipher
import javax.crypto.CipherSpi
import javax.crypto.spec.SecretKeySpec

class ParametersIgnoredTest {

    class DrawsItsOwnNonce : CipherSpi() {
        private val nonce = ByteArray(12).also { SecureRandom().nextBytes(it) }
        override fun engineSetMode(mode: String?) = Unit
        override fun engineSetPadding(padding: String?) = Unit
        override fun engineGetBlockSize() = 0
        override fun engineGetOutputSize(inputLen: Int) = inputLen
        override fun engineGetIV(): ByteArray = nonce
        override fun engineGetParameters(): AlgorithmParameters? = null
        override fun engineInit(opmode: Int, key: Key?, random: SecureRandom?) = Unit
        override fun engineInit(opmode: Int, key: Key?, params: AlgorithmParameterSpec?, random: SecureRandom?) = Unit
        override fun engineInit(opmode: Int, key: Key?, params: AlgorithmParameters?, random: SecureRandom?) = Unit
        override fun engineUpdate(input: ByteArray?, offset: Int, len: Int): ByteArray = ByteArray(0)
        override fun engineUpdate(input: ByteArray?, offset: Int, len: Int, output: ByteArray?, outputOffset: Int) = 0
        override fun engineDoFinal(input: ByteArray?, offset: Int, len: Int): ByteArray = ByteArray(len)
        override fun engineDoFinal(input: ByteArray?, offset: Int, len: Int, output: ByteArray?, outputOffset: Int) = 0
    }

    private object Ignoring : Provider("Ignoring", "1", "draws its own nonce") {
        private fun readResolve(): Any = Ignoring
        init { put("Cipher.IgnoresNonce", DrawsItsOwnNonce::class.java.name) }
    }

    private val key = KeyMaterial.Secret(SecretKeySpec(ByteArray(16), "AES"))
    private fun parameters(tree: Map<String, Any>) = ParameterBinder().bind(tree, "parameters")
    private val gcm = mapOf("class" to "javax.crypto.spec.GCMParameterSpec", "arguments" to listOf(128, "fresh(12)"))
    private fun case(algorithm: String, provider: String) = BenchmarkCase(type = "Cipher", algorithm = algorithm, provider = provider, operation = Operation.ENCRYPT, phase = Phase.WARM)

    @Test
    fun aProviderDrawingItsOwnNonceIsNamed() {
        Security.addProvider(Ignoring)
        try {
            val reason = EncryptDefinition.parametersIgnored(case("IgnoresNonce", "Ignoring"), key, parameters(gcm))
            assertTrue(reason, reason!!.startsWith("parameters_ignored: Ignoring accepted GCMParameterSpec"))
        } finally {
            Security.removeProvider("Ignoring")
        }
    }

    @Test
    fun aProviderUsingTheNonceIsNotNamed() = assertEquals(null, EncryptDefinition.parametersIgnored(case("AES/GCM/NoPadding", "SunJCE"), key, parameters(gcm)))

    @Test
    fun noParametersNothingToTell() = assertEquals(null, EncryptDefinition.parametersIgnored(case("AES/ECB/NoPadding", "SunJCE"), key, null))
}
