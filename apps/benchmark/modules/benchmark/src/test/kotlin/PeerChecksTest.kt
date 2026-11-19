package io.github.junekim0007.cryptobench.benchmark

import io.github.junekim0007.cryptobench.benchmark.run.HostHarness
import io.github.junekim0007.cryptobench.benchmark.run.OutputHook
import io.github.junekim0007.cryptobench.benchmark.verify.oracle.CheckedCall
import io.github.junekim0007.cryptobench.benchmark.verify.oracle.cross.CipherPeer
import io.github.junekim0007.cryptobench.benchmark.verify.oracle.cross.KeyOutputPeer
import io.github.junekim0007.cryptobench.benchmark.verify.oracle.cross.PeerCheck
import io.github.junekim0007.cryptobench.benchmark.verify.oracle.cross.RecomputePeer
import io.github.junekim0007.cryptobench.benchmark.verify.oracle.cross.SignaturePeer
import io.github.junekim0007.cryptobench.preparation.input.InputBytes
import io.github.junekim0007.cryptobench.preparation.input.OperationInput
import io.github.junekim0007.cryptobench.preparation.peer.Outcome
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyRecipe
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.operation.Invocations
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import org.junit.Assert.assertEquals
import org.junit.Test
import java.security.KeyPair
import java.security.KeyPairGenerator
import java.security.Signature
import javax.crypto.Cipher
import javax.crypto.KeyGenerator

/** Characterization: each peer check over a call on the JDK's own providers; a peer may be the case's own provider here. Reasons cut to their code and exception. */
class PeerChecksTest {

    private val message = InputBytes.of(0, 16)

    private fun pair(algorithm: String, provider: String, bits: Int): KeyPair =
        KeyPairGenerator.getInstance(algorithm, provider).apply { initialize(bits) }.generateKeyPair()

    private fun prepared(type: String, algorithm: String, provider: String, operation: Operation, key: KeyMaterial, input: OperationInput, recipe: KeyRecipe = KeyRecipe.None) =
        PreparedCase(BenchmarkCase(type, algorithm, provider, operation, inputSize = 16), recipe, key, null, null, input)
            .let { it.copy(perCall = Invocations.of(it).perCall) }

    // judgedAs: the case the check sees, where a test swaps what the call ran with
    private fun judged(check: PeerCheck, prepared: PreparedCase, peer: String, judgedAs: PreparedCase = prepared, output: (Any?) -> Any? = { it }): String = PeerProvider.installed {
        val invocation = Invocations.of(prepared)
        val hook = OutputHook()
        HostHarness.ONCE.call(invocation, hook)
        when (val outcome = check.against(CheckedCall(judgedAs, invocation, output(hook.outputs.single())), peer)) {
            Outcome.Pass -> "pass"
            is Outcome.Fail -> "fail ${cut(outcome.reason)}"
            is Outcome.NotCheckable -> "not_checkable ${cut(outcome.reason)}"
        }
    }

    private fun cut(reason: String) = reason.split(": ").take(2).joinToString(": ")

    private fun flipped(output: Any?) = (output as ByteArray).copyOf().also { it[0] = (it[0].toInt() xor 1).toByte() }

    @Test
    fun cipherPeer() {
        val secret = KeyMaterial.Secret(KeyGenerator.getInstance("AES", "SunJCE").apply { init(128) }.generateKey())
        val encrypt = CheckFixture.gcmEncrypt()
        val ecb = Cipher.getInstance("AES/ECB/PKCS5Padding", "SunJCE").apply { init(Cipher.ENCRYPT_MODE, secret.key) }.doFinal(message)
        val decrypt = prepared("Cipher", "AES/ECB/PKCS5Padding", "SunJCE", Operation.DECRYPT, secret, OperationInput.Ciphertext(ecb, 16, null, null))
        val table = listOf(
            "encrypt gcm" to judged(CipherPeer, encrypt, "SunJCE"),
            "encrypt gcm, flipped output" to judged(CipherPeer, encrypt, "SunJCE", output = ::flipped),
            "encrypt gcm, output not bytes" to judged(CipherPeer, encrypt, "SunJCE", output = { 7 }),
            "encrypt gcm, peer without AES" to judged(CipherPeer, encrypt, PeerProvider.NAME),
            "decrypt ecb" to judged(CipherPeer, decrypt, "SunJCE"),
            "decrypt ecb, flipped output" to judged(CipherPeer, decrypt, "SunJCE", output = ::flipped),
            "decrypt without ciphertext input" to judged(CipherPeer, decrypt, "SunJCE", decrypt.copy(input = OperationInput.Message(message))),
        )
        assertEquals(listOf(
            "encrypt gcm" to "pass",
            "encrypt gcm, flipped output" to "fail peer_refused: AEADBadTagException",
            "encrypt gcm, output not bytes" to "fail not_bytes: Integer",
            "encrypt gcm, peer without AES" to "not_checkable peer_unavailable: NoSuchAlgorithmException",
            "decrypt ecb" to "pass",
            "decrypt ecb, flipped output" to "fail peer_differs: the peer decrypts the same ciphertext to other bytes than the case's output",
            "decrypt without ciphertext input" to "not_checkable no_ciphertext_input",
        ), table)
    }

    @Test
    fun signaturePeer() {
        val keys = KeyMaterial.Pairs(listOf(pair("EC", "SunEC", 256)))
        val sign = prepared("Signature", "SHA256withECDSA", "SunEC", Operation.SIGN, keys, OperationInput.Message(message))
        val signature = Signature.getInstance("SHA256withECDSA", "SunEC").apply { initSign(keys.pairs.first().private); update(message) }.sign()
        val verify = prepared("Signature", "SHA256withECDSA", "SunEC", Operation.VERIFY, keys, OperationInput.SignedMessage(message, signature, null))
        val other = KeyMaterial.Pairs(listOf(pair("EC", "SunEC", 256)))
        val table = listOf(
            "sign" to judged(SignaturePeer, sign, "SunEC"),
            "sign, garbage signature" to judged(SignaturePeer, sign, "SunEC", output = { ByteArray(8) }),
            "sign, another key's signature" to judged(SignaturePeer, sign, "SunEC", sign.copy(key = other)),
            "verify" to judged(SignaturePeer, verify, "SunEC"),
            "verify without signed input" to judged(SignaturePeer, verify, "SunEC", verify.copy(input = OperationInput.Message(message))),
            "sign without a key pair" to judged(SignaturePeer, sign, "SunEC", sign.copy(key = KeyMaterial.None)),
            "sign, peer without the algorithm" to judged(SignaturePeer, sign, "SunRsaSign"),
        )
        assertEquals(listOf(
            "sign" to "pass",
            "sign, garbage signature" to "fail peer_refused: SignatureException",
            "sign, another key's signature" to "fail peer_rejects: the peer does not verify the case's signature",
            "verify" to "pass",
            "verify without signed input" to "not_checkable no_signed_input",
            "sign without a key pair" to "not_checkable no_key_pair",
            "sign, peer without the algorithm" to "not_checkable peer_unavailable: NoSuchAlgorithmException",
        ), table)
    }

    @Test
    fun keyOutputPeer() {
        val pairCase = prepared("KeyPairGenerator", "EC", "SunEC", Operation.GENERATE_KEY_PAIR, KeyMaterial.None, OperationInput.None, KeyRecipe.Pair("EC", 256, "SunEC"))
        val secretCase = prepared("KeyGenerator", "AES", "SunJCE", Operation.GENERATE_KEY, KeyMaterial.None, OperationInput.None, KeyRecipe.Secret("AES", 128, "SunJCE"))
        val table = listOf(
            "key pair" to judged(KeyOutputPeer, pairCase, "SunEC"),
            "key pair, peer without the KeyFactory" to judged(KeyOutputPeer, pairCase, "SunJCE"),
            "secret key" to judged(KeyOutputPeer, secretCase, "SunJCE"),
        )
        assertEquals(listOf(
            "key pair" to "pass",
            "key pair, peer without the KeyFactory" to "not_checkable peer_key_rejected: no KeyFactory of SunJCE rebuilds the EC PKCS#8 encoding",
            "secret key" to "not_checkable no_peer_check: a generated secret key has nothing a peer recomputes",
        ), table)
    }

    @Test
    fun agreementRecompute() {
        val ec = KeyMaterial.Pairs(listOf(pair("EC", "SunEC", 256), pair("EC", "SunEC", 256)))
        val dh = KeyMaterial.Pairs(listOf(pair("DH", "SunJCE", 2048), pair("DH", "SunJCE", 2048)))
        val ecdh = prepared("KeyAgreement", "ECDH", "SunEC", Operation.AGREE_KEY, ec, OperationInput.None)
        val table = listOf(
            "ecdh" to judged(RecomputePeer, ecdh, "SunEC"),
            "ecdh, flipped output" to judged(RecomputePeer, ecdh, "SunEC", output = ::flipped),
            "dh" to judged(RecomputePeer, prepared("KeyAgreement", "DH", "SunJCE", Operation.AGREE_KEY, dh, OperationInput.None), "SunJCE"),
            "ecdh, peer without ECDH" to judged(RecomputePeer, ecdh, "SunJCE"),
        )
        assertEquals(listOf(
            "ecdh" to "pass",
            "ecdh, flipped output" to "fail peer_differs: the peer computes other bytes from the same key, parameters and input",
            "dh" to "pass",
            "ecdh, peer without ECDH" to "not_checkable peer_key_rejected: no KeyFactory of SunJCE rebuilds the EC PKCS#8 encoding",
        ), table)
    }
}
