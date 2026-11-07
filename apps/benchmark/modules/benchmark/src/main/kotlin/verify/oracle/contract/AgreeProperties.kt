package io.github.junekim0007.cryptobench.benchmark.verify.oracle.contract

import io.github.junekim0007.cryptobench.benchmark.verify.oracle.CheckedCall
import io.github.junekim0007.cryptobench.preparation.interop.report.Outcome
import javax.crypto.KeyAgreement

/** Key agreement: the peer, from its own private key and the case's public key, derives the same secret. */
internal object AgreeProperties : Properties {

    override fun of(call: CheckedCall): Map<String, Outcome> {
        val output = call.output as? ByteArray ?: return mapOf("output" to Outcome.Fail("not_bytes: ${call.output?.javaClass?.simpleName}"))
        val pairs = call.prepared.key.keyPairsOrNull ?: return mapOf("peer" to Outcome.NotCheckable("no_key_pairs"))
        val spec = call.prepared.parameters?.next()
        val peer = runCatching {
            val agreement = KeyAgreement.getInstance(call.prepared.case.algorithm, call.prepared.case.provider)
            if (spec == null) agreement.init(pairs.last().private) else agreement.init(pairs.last().private, spec)
            agreement.doPhase(pairs.first().public, true)
            agreement.generateSecret()
        }
        return mapOf("peer" to holds(peer.getOrNull()?.contentEquals(output) == true) {
            peer.exceptionOrNull()?.let { "peer_failed: ${it.javaClass.simpleName}: ${it.message}" } ?: "peer_differs: the peer derived another secret"
        })
    }
}
