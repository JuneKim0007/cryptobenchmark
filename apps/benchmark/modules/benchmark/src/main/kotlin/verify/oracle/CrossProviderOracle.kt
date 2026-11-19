package io.github.junekim0007.cryptobench.benchmark.verify.oracle

import io.github.junekim0007.cryptobench.preparation.peer.Consumer
import io.github.junekim0007.cryptobench.preparation.peer.Outcome
import io.github.junekim0007.cryptobench.preparation.peer.PeerEngine
import io.github.junekim0007.cryptobench.preparation.peer.ProducedCall
import io.github.junekim0007.cryptobench.preparation.peer.Travel
import io.github.junekim0007.cryptobench.preparation.port.Availability
import io.github.junekim0007.cryptobench.preparation.port.DeviceCapability

/** Every other installed provider of the case's service checks the call's own output through the peer engine, from the case's key, parameters and input. */
class CrossProviderOracle(private val capability: DeviceCapability) : Oracle {

    override val name = "crossProvider"

    private val engine = PeerEngine(capability)

    override fun judge(call: CheckedCall): Judgement {
        val case = call.prepared.case
        if (!PeerEngine.checks(case.operation)) return Judgement(Outcome.NotCheckable("no_peer_check: ${case.operation}"))
        val peers = capability.providers().filter { it != case.provider && capability.check(it, case.type, case.algorithm) == Availability.Available }
        if (peers.isEmpty()) return Judgement(Outcome.NotCheckable("no_peer_provider: ${case.type}.${case.algorithm}"))
        val produced = ProducedCall(call.prepared, call.invocation.engine, call.output)
        val byPeer = peers.associateWith { peer -> engine.check(produced, Consumer(peer, case.algorithm), Travel.USED) }
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
}
