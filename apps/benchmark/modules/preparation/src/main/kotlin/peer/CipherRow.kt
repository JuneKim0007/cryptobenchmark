package io.github.junekim0007.cryptobench.preparation.peer

import io.github.junekim0007.cryptobench.preparation.input.CipherKeys
import io.github.junekim0007.cryptobench.preparation.input.OperationInput
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.operation.CaseArguments
import java.security.AlgorithmParameters
import java.security.spec.AlgorithmParameterSpec
import javax.crypto.Cipher

/** Encrypt: the consumer decrypts the ciphertext under the call's key and parameters to its input. Decrypt: the consumer decrypts the same ciphertext to the call's output. */
internal object CipherRow : ConsumingRow {

    override val mode = PeerEngine.PRODUCE_CONSUME

    override fun ready(produced: ProducedCall): Outcome? {
        if (OutputBytes.of(produced.output) == null) return Outcome.Fail("not_bytes: ${produced.output?.javaClass?.simpleName}")
        return when {
            encrypts(produced) -> if (produced.engine is Cipher) null else Outcome.NotCheckable("no_engine_read_back")
            produced.prepared.input is OperationInput.Ciphertext -> null
            else -> Outcome.NotCheckable("no_ciphertext_input")
        }
    }

    override fun setup(produced: ProducedCall, consumer: Consumer, travel: Travel): () -> Any? {
        if (encrypts(produced)) {
            val cipher = decrypting(produced, consumer, PeerParameters.used(produced.prepared, (produced.engine as Cipher).parameters, travel))
            val output = OutputBytes.of(produced.output)!!
            return { cipher.doFinal(output) }
        }
        val input = produced.prepared.input as OperationInput.Ciphertext
        val cipher = decrypting(produced, consumer, travel.carried(input.spec ?: input.providerParameters?.let(PeerParameters::portable)))
        return { cipher.doFinal(input.bytes) }
    }

    override fun judge(produced: ProducedCall, consumed: Any?): Outcome =
        if (encrypts(produced)) {
            agrees((consumed as ByteArray).contentEquals(CaseArguments.preparedMessage(produced.prepared)), "peer_differs: the peer decrypts the case's ciphertext to other bytes than its input")
        } else {
            agrees((consumed as ByteArray).contentEquals(OutputBytes.of(produced.output)), "peer_differs: the peer decrypts the same ciphertext to other bytes than the case's output")
        }

    private fun encrypts(produced: ProducedCall) = produced.prepared.case.operation == Operation.ENCRYPT

    private fun decrypting(produced: ProducedCall, consumer: Consumer, parameters: Any?): Cipher {
        val cipher = Cipher.getInstance(consumer.algorithm, consumer.provider)
        val key = PeerKey.of(CipherKeys.decrypting(produced.prepared.key), consumer.provider)
        return cipher.apply {
            when (parameters) {
                null -> init(Cipher.DECRYPT_MODE, key)
                is AlgorithmParameterSpec -> init(Cipher.DECRYPT_MODE, key, parameters)
                is AlgorithmParameters -> init(Cipher.DECRYPT_MODE, key, parameters)
                else -> throw PeerRefusal("parameters_not_recoverable", parameters.javaClass.simpleName)
            }
        }
    }
}
