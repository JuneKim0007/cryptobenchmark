package io.github.junekim0007.cryptobench.benchmark.verify.oracle

import io.github.junekim0007.cryptobench.benchmark.verify.oracle.cross.CipherPeer
import io.github.junekim0007.cryptobench.benchmark.verify.oracle.cross.KeyOutputPeer
import io.github.junekim0007.cryptobench.benchmark.verify.oracle.cross.PeerCheck
import io.github.junekim0007.cryptobench.benchmark.verify.oracle.cross.RecomputePeer
import io.github.junekim0007.cryptobench.benchmark.verify.oracle.cross.SignaturePeer
import io.github.junekim0007.cryptobench.preparation.interop.report.Outcome
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.port.Availability
import io.github.junekim0007.cryptobench.preparation.port.DeviceCapability

/** Every other installed provider of the case's service checks the call's own output, from the case's key, parameters and input. */
class CrossProviderOracle(private val capability: DeviceCapability) : Oracle {

    override val name = "crossProvider"

    override fun judge(call: CheckedCall): Judgement {
        val case = call.prepared.case
        val check = CHECKS[case.operation] ?: return Judgement(Outcome.NotCheckable("no_peer_check: ${case.operation}"))
        val peers = capability.providers().filter { it != case.provider && capability.check(it, case.type, case.algorithm) == Availability.Available }
        if (peers.isEmpty()) return Judgement(Outcome.NotCheckable("no_peer_provider: ${case.type}.${case.algorithm}"))
        val byPeer = peers.associateWith { peer -> check.against(call, peer) }
        val outcome = when {
            byPeer.values.any { it is Outcome.Fail } -> Outcome.Fail(reasons(byPeer) { it is Outcome.Fail })
            byPeer.values.any { it == Outcome.Pass } -> Outcome.Pass
            else -> Outcome.NotCheckable(reasons(byPeer) { it is Outcome.NotCheckable })
        }
        return Judgement(outcome, mapOf("peers" to byPeer.mapValuesTo(LinkedHashMap()) { (_, verdict) -> verdict.label }))
    }

    private fun reasons(byPeer: Map<String, Outcome>, kept: (Outcome) -> Boolean) =
        byPeer.filterValues(kept).entries.joinToString("; ") { (peer, outcome) ->
            "$peer: ${(outcome as? Outcome.Fail)?.reason ?: (outcome as Outcome.NotCheckable).reason}"
        }

    private companion object {
        val CHECKS: Map<Operation, PeerCheck> = mapOf(
            Operation.ENCRYPT to CipherPeer,
            Operation.DECRYPT to CipherPeer,
            Operation.SIGN to SignaturePeer,
            Operation.VERIFY to SignaturePeer,
            Operation.DIGEST to RecomputePeer,
            Operation.COMPUTE_MAC to RecomputePeer,
            Operation.AGREE_KEY to RecomputePeer,
            Operation.GENERATE_KEY to KeyOutputPeer,
            Operation.GENERATE_KEY_PAIR to KeyOutputPeer,
        )
    }
}
