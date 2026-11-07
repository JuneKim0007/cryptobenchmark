package io.github.junekim0007.cryptobench.benchmark.verify.oracle.cross

import io.github.junekim0007.cryptobench.benchmark.verify.OutputBytes
import io.github.junekim0007.cryptobench.benchmark.verify.oracle.CheckedCall
import io.github.junekim0007.cryptobench.preparation.input.CipherKeys
import io.github.junekim0007.cryptobench.preparation.input.OperationInput
import io.github.junekim0007.cryptobench.preparation.interop.report.Outcome
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import java.security.AlgorithmParameters
import java.security.Key
import java.security.spec.AlgorithmParameterSpec
import javax.crypto.Cipher

/** Encrypt: the peer decrypts the case's ciphertext under its key and parameters to the case's input. Decrypt: the peer decrypts the same ciphertext to the case's output. */
internal object CipherPeer : PeerCheck {

    override fun against(call: CheckedCall, peer: String): Outcome {
        val prepared = call.prepared
        val output = OutputBytes.of(call.output) ?: return Outcome.Fail("not_bytes: ${call.output?.javaClass?.simpleName}")
        return if (prepared.case.operation == Operation.ENCRYPT) {
            val engine = call.invocation.engine as? Cipher ?: return Outcome.NotCheckable("no_engine_read_back")
            val message = (prepared.input as? OperationInput.Message)?.bytes ?: ByteArray(prepared.case.inputSize ?: 0)
            PeerRun.of({ decrypting(call, peer, PeerParameters.used(prepared, engine.parameters)) }) { cipher ->
                PeerRun.agrees(cipher.doFinal(output).contentEquals(message), "peer_differs: the peer decrypts the case's ciphertext to other bytes than its input")
            }
        } else {
            val input = prepared.input as? OperationInput.Ciphertext ?: return Outcome.NotCheckable("no_ciphertext_input")
            PeerRun.of({ decrypting(call, peer, input.spec ?: input.providerParameters?.let(PeerParameters::portable)) }) { cipher ->
                PeerRun.agrees(cipher.doFinal(input.bytes).contentEquals(output), "peer_differs: the peer decrypts the same ciphertext to other bytes than the case's output")
            }
        }
    }

    private fun decrypting(call: CheckedCall, peer: String, parameters: Any?): Cipher {
        val key: Key = PeerKey.of(CipherKeys.decrypting(call.prepared.key), peer)
        return Cipher.getInstance(call.prepared.case.algorithm, peer).apply {
            when (parameters) {
                null -> init(Cipher.DECRYPT_MODE, key)
                is AlgorithmParameterSpec -> init(Cipher.DECRYPT_MODE, key, parameters)
                is AlgorithmParameters -> init(Cipher.DECRYPT_MODE, key, parameters)
                else -> throw PeerRefusal("parameters_not_recoverable", parameters.javaClass.simpleName)
            }
        }
    }
}
