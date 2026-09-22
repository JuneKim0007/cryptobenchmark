package io.github.junekim0007.cryptobench.preparation.check

import io.github.junekim0007.cryptobench.preparation.engine.CaseEngines
import io.github.junekim0007.cryptobench.preparation.input.CipherKeys
import io.github.junekim0007.cryptobench.preparation.input.OperationInput
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import java.security.KeyPairGenerator
import java.security.MessageDigest
import javax.crypto.Cipher
import javax.crypto.KeyAgreement
import javax.crypto.KeyGenerator
import javax.crypto.Mac

class CaseCheck {

    fun check(prepared: PreparedCase) {
        val case = prepared.case
        val key = prepared.key
        when (case.operation) {
            Operation.ENCRYPT -> encrypt(prepared)
            Operation.DECRYPT -> decrypt(prepared)
            Operation.SIGN -> sign(prepared)
            Operation.VERIFY -> verify(prepared)
            Operation.DIGEST -> MessageDigest.getInstance(case.algorithm, case.provider).digest(message(prepared))
            Operation.COMPUTE_MAC -> Mac.getInstance(case.algorithm, case.provider)
                .apply { init(secret(key)) }.doFinal(message(prepared))
            Operation.GENERATE_KEY -> KeyGenerator.getInstance(case.algorithm, case.provider)
                .also { generator -> case.keySize?.let { generator.init(it) } }.generateKey()
            Operation.GENERATE_KEY_PAIR -> KeyPairGenerator.getInstance(case.algorithm, case.provider)
                .also { generator -> case.keySize?.let { generator.initialize(it) } }.generateKeyPair()
            Operation.AGREE_KEY -> agree(prepared)
            Operation.TYPE_DEFAULT -> Unit
        }
    }

    private fun encrypt(prepared: PreparedCase) {
        val cipher = CaseEngines.cipher(prepared.case)
        val key = CipherKeys.encrypting(prepared.key)
        val spec = prepared.parameters?.next()
        if (spec == null) cipher.init(Cipher.ENCRYPT_MODE, key) else cipher.init(Cipher.ENCRYPT_MODE, key, spec)
        cipher.doFinal(message(prepared))
    }

    private fun decrypt(prepared: PreparedCase) {
        val input = prepared.input as? OperationInput.Ciphertext ?: throw IllegalArgumentException("decrypt_without_ciphertext")
        val cipher = CaseEngines.cipher(prepared.case)
        input.initDecrypting(cipher, CipherKeys.decrypting(prepared.key))
        check(cipher.doFinal(input.bytes).size == input.plaintextSize) { "decrypt_size_mismatch" }
    }

    private fun sign(prepared: PreparedCase) {
        val signature = CaseEngines.signature(prepared.case)
        prepared.parameters?.next()?.let { signature.setParameter(it) }
        signature.initSign(pair(prepared.key).private)
        signature.update(message(prepared))
        signature.sign()
    }

    private fun verify(prepared: PreparedCase) {
        val input = prepared.input as? OperationInput.SignedMessage ?: throw IllegalArgumentException("verify_without_signature")
        val signature = CaseEngines.signature(prepared.case)
        prepared.parameters?.next()?.let { signature.setParameter(it) }
        signature.initVerify(pair(prepared.key).public)
        signature.update(input.message)
        check(signature.verify(input.signature)) { "verify_failed" }
    }

    private fun agree(prepared: PreparedCase) {
        val pairs = prepared.key.keyPairsOrNull ?: throw IllegalArgumentException("agreement_needs_key_pairs")
        KeyAgreement.getInstance(prepared.case.algorithm, prepared.case.provider).apply {
            init(pairs.first().private)
            doPhase(pairs.last().public, true)
        }.generateSecret()
    }

    private fun message(prepared: PreparedCase): ByteArray =
        (prepared.input as? OperationInput.Message)?.bytes ?: ByteArray(prepared.case.inputSize ?: 0)

    private fun secret(key: KeyMaterial) =
        key.secretKeyOrNull ?: throw IllegalArgumentException("mac_needs_a_secret_key")

    private fun pair(key: KeyMaterial) =
        key.keyPairsOrNull?.first() ?: throw IllegalArgumentException("signature_needs_a_key_pair")
}
