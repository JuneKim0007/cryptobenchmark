package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.input.InputBytes
import io.github.junekim0007.cryptobench.preparation.input.OperationInput
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyRecipe
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.operation.Invocations
import io.github.junekim0007.cryptobench.preparation.parameter.bind.ParameterBinder
import io.github.junekim0007.cryptobench.preparation.peer.Consumer
import io.github.junekim0007.cryptobench.preparation.peer.Outcome
import io.github.junekim0007.cryptobench.preparation.peer.PeerEngine
import io.github.junekim0007.cryptobench.preparation.peer.ProducedCall
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import org.junit.Assert.assertEquals
import org.junit.Test
import java.security.KeyPair
import java.security.KeyPairGenerator
import java.security.Signature
import javax.crypto.Cipher
import javax.crypto.KeyGenerator

/** Characterization: each peer row over a call on the JDK's own providers; a consumer may be the case's own provider here. Reasons cut to their code and exception. */
class PeerRowsTest {

    private val message = InputBytes.of(0, 16)

    private fun pair(algorithm: String, provider: String, bits: Int): KeyPair =
        KeyPairGenerator.getInstance(algorithm, provider).apply { initialize(bits) }.generateKeyPair()

    private fun prepared(type: String, algorithm: String, provider: String, operation: Operation, key: KeyMaterial, input: OperationInput,
                         recipe: KeyRecipe = KeyRecipe.None, parameters: Map<String, Any>? = null) =
        PreparedCase(BenchmarkCase(type, algorithm, provider, operation, inputSize = 16), recipe, key, parameters?.let { ParameterBinder().bind(it, "parameters") }, null, input)

    // judgedAs: the case the engine sees, where a test swaps what the call ran with
    private fun judged(prepared: PreparedCase, consumer: String, judgedAs: PreparedCase = prepared, output: (Any?) -> Any? = { it }): String {
        val invocation = Invocations.of(prepared)
        val produced = ProducedCall(judgedAs, invocation.engine, output(invocation.once()))
        return when (val outcome = PeerEngine.check(produced, Consumer(consumer, judgedAs.case.algorithm))) {
            Outcome.Pass -> "pass"
            is Outcome.Fail -> "fail ${cut(outcome.reason)}"
            is Outcome.NotCheckable -> "not_checkable ${cut(outcome.reason)}"
        }
    }

    private fun cut(reason: String) = reason.split(": ").take(2).joinToString(": ")

    private fun flipped(output: Any?) = (output as ByteArray).copyOf().also { it[0] = (it[0].toInt() xor 1).toByte() }

    @Test
    fun cipherRow() {
        val secret = KeyMaterial.Secret(KeyGenerator.getInstance("AES", "SunJCE").apply { init(128) }.generateKey())
        val gcm = mapOf("class" to "javax.crypto.spec.GCMParameterSpec", "arguments" to listOf(128, "fresh(12)"))
        val encrypt = prepared("Cipher", "AES/GCM/NoPadding", "SunJCE", Operation.ENCRYPT, secret, OperationInput.Message(message), parameters = gcm)
        val ecb = Cipher.getInstance("AES/ECB/PKCS5Padding", "SunJCE").apply { init(Cipher.ENCRYPT_MODE, secret.key) }.doFinal(message)
        val decrypt = prepared("Cipher", "AES/ECB/PKCS5Padding", "SunJCE", Operation.DECRYPT, secret, OperationInput.Ciphertext(ecb, 16, null, null))
        val table = listOf(
            "encrypt gcm" to judged(encrypt, "SunJCE"),
            "encrypt gcm, flipped output" to judged(encrypt, "SunJCE", output = ::flipped),
            "encrypt gcm, output not bytes" to judged(encrypt, "SunJCE", output = { 7 }),
            "encrypt gcm, consumer without AES" to judged(encrypt, "SUN"),
            "decrypt ecb" to judged(decrypt, "SunJCE"),
            "decrypt ecb, flipped output" to judged(decrypt, "SunJCE", output = ::flipped),
            "decrypt without ciphertext input" to judged(decrypt, "SunJCE", decrypt.copy(input = OperationInput.Message(message))),
        )
        assertEquals(listOf(
            "encrypt gcm" to "pass",
            "encrypt gcm, flipped output" to "fail peer_refused: AEADBadTagException",
            "encrypt gcm, output not bytes" to "fail not_bytes: Integer",
            "encrypt gcm, consumer without AES" to "not_checkable peer_unavailable: NoSuchAlgorithmException",
            "decrypt ecb" to "pass",
            "decrypt ecb, flipped output" to "fail peer_differs: the peer decrypts the same ciphertext to other bytes than the case's output",
            "decrypt without ciphertext input" to "not_checkable no_ciphertext_input",
        ), table)
    }

    @Test
    fun signatureRow() {
        val keys = KeyMaterial.Pairs(listOf(pair("EC", "SunEC", 256)))
        val sign = prepared("Signature", "SHA256withECDSA", "SunEC", Operation.SIGN, keys, OperationInput.Message(message))
        val signature = Signature.getInstance("SHA256withECDSA", "SunEC").apply { initSign(keys.pairs.first().private); update(message) }.sign()
        val verify = prepared("Signature", "SHA256withECDSA", "SunEC", Operation.VERIFY, keys, OperationInput.SignedMessage(message, signature, null))
        val other = KeyMaterial.Pairs(listOf(pair("EC", "SunEC", 256)))
        val table = listOf(
            "sign" to judged(sign, "SunEC"),
            "sign, garbage signature" to judged(sign, "SunEC", output = { ByteArray(8) }),
            "sign, another key's signature" to judged(sign, "SunEC", sign.copy(key = other)),
            "verify" to judged(verify, "SunEC"),
            "verify without signed input" to judged(verify, "SunEC", verify.copy(input = OperationInput.Message(message))),
            "sign without a key pair" to judged(sign, "SunEC", sign.copy(key = KeyMaterial.None)),
            "sign, consumer without the algorithm" to judged(sign, "SunRsaSign"),
        )
        assertEquals(listOf(
            "sign" to "pass",
            "sign, garbage signature" to "fail peer_refused: SignatureException",
            "sign, another key's signature" to "fail peer_rejects: the peer does not verify the case's signature",
            "verify" to "pass",
            "verify without signed input" to "not_checkable no_signed_input",
            "sign without a key pair" to "not_checkable no_key_pair",
            "sign, consumer without the algorithm" to "not_checkable peer_unavailable: NoSuchAlgorithmException",
        ), table)
    }

    @Test
    fun keyOutputRow() {
        val pairCase = prepared("KeyPairGenerator", "EC", "SunEC", Operation.GENERATE_KEY_PAIR, KeyMaterial.None, OperationInput.None, KeyRecipe.Pair("EC", 256, "SunEC"))
        val secretCase = prepared("KeyGenerator", "AES", "SunJCE", Operation.GENERATE_KEY, KeyMaterial.None, OperationInput.None, KeyRecipe.Secret("AES", 128, "SunJCE"))
        val table = listOf(
            "key pair" to judged(pairCase, "SunEC"),
            "key pair, consumer without the KeyFactory" to judged(pairCase, "SunJCE"),
            "secret key" to judged(secretCase, "SunJCE"),
        )
        assertEquals(listOf(
            "key pair" to "pass",
            "key pair, consumer without the KeyFactory" to "not_checkable peer_key_rejected: no KeyFactory of SunJCE rebuilds the EC PKCS#8 encoding",
            "secret key" to "not_checkable no_peer_check: a generated secret key has nothing a peer recomputes",
        ), table)
    }

    @Test
    fun recomputeRow() {
        val ec = KeyMaterial.Pairs(listOf(pair("EC", "SunEC", 256), pair("EC", "SunEC", 256)))
        val dh = KeyMaterial.Pairs(listOf(pair("DH", "SunJCE", 2048), pair("DH", "SunJCE", 2048)))
        val ecdh = prepared("KeyAgreement", "ECDH", "SunEC", Operation.AGREE_KEY, ec, OperationInput.None)
        val table = listOf(
            "ecdh" to judged(ecdh, "SunEC"),
            "ecdh, flipped output" to judged(ecdh, "SunEC", output = ::flipped),
            "dh" to judged(prepared("KeyAgreement", "DH", "SunJCE", Operation.AGREE_KEY, dh, OperationInput.None), "SunJCE"),
            "ecdh, consumer without ECDH" to judged(ecdh, "SunJCE"),
        )
        assertEquals(listOf(
            "ecdh" to "pass",
            "ecdh, flipped output" to "fail peer_differs: the peer computes other bytes from the same key, parameters and input",
            "dh" to "pass",
            "ecdh, consumer without ECDH" to "not_checkable peer_key_rejected: no KeyFactory of SunJCE rebuilds the EC PKCS#8 encoding",
        ), table)
    }
}
