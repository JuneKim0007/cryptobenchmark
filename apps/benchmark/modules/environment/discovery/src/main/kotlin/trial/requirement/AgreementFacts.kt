package io.github.junekim0007.cryptobench.discovery.trial.requirement

import io.github.junekim0007.cryptobench.discovery.contract.ServiceRequirement
import java.security.InvalidKeyException
import java.security.KeyPair
import javax.crypto.KeyAgreement

internal object AgreementFacts : RequirementCall {

    override fun instance(service: ProbedService) {
        KeyAgreement.getInstance(service.algorithm, service.provider)
    }

    override fun measure(service: ProbedService, sheet: FactSheet): CallResult {
        val tried = mutableListOf<Map<String, Any>>()
        var detail = ""
        for (key in service.keys.of(service.type, service.algorithm, service.provider, pairsOnly = true)) {
            val peer = runCatching { service.keys.peer(key) }.getOrElse {
                tried += key.describe() + ("refused" to ErrorText.of(it))
                null
            } ?: continue
            val refused = runCatching { agree(service.algorithm, service, key.pair!!, peer) }.exceptionOrNull() ?: return measured(service, sheet, key, peer, tried)
            detail = ErrorText.of(refused)
            tried += key.describe() + ("refused" to detail)
        }
        val reason = when {
            tried.isEmpty() -> ServiceRequirement.NO_KEY
            detail.startsWith(InvalidKeyException::class.java.simpleName) -> ServiceRequirement.KEY_REFUSED
            else -> ServiceRequirement.PARAMETERS_UNKNOWN
        }
        return CallResult(reason, detail, keysTried = tried)
    }

    private fun measured(service: ProbedService, sheet: FactSheet, key: ProbeKey, peer: KeyPair, tried: List<Map<String, Any>>): CallResult {
        val own = key.pair!!
        val secret = agree(service.algorithm, service, own, peer)
        sheet.measure("secretBytes") { secret.size }
        sheet.measure("bothSidesAgree") { secret.contentEquals(agree(service.algorithm, service, peer, own)) }
        sheet.measure("deterministic") { secret.contentEquals(agree(service.algorithm, service, own, peer)) }
        sheet.measure("withoutPeer") { ErrorText.refusal { KeyAgreement.getInstance(service.algorithm, service.provider).run { init(own.private); generateSecret() } } ?: "ok" }
        service.secretNames.firstOrNull()?.let { name ->
            sheet.measure("secretAsKey") {
                linkedMapOf("name" to name, "result" to (ErrorText.refusal {
                    KeyAgreement.getInstance(service.algorithm, service.provider).run { init(own.private); doPhase(peer.public, true); generateSecret(name) }
                } ?: "ok"))
            }
        }
        if (service.keys.sizable(key)) sheet.measure("keyBits") { keyBits(service, key) }
        sheet.measure("peerOfOtherSize") { peerOfOtherSize(service, key) }
        sheet.measure("foreignKeys") { ForeignKeys.of(service, key) { other -> agree(service.algorithm, service, other.pair!!, service.keys.peer(other)) } }
        sheet.measure("reset") { reset(service, own, peer) }
        return CallResult(
            key = key,
            runWith = mapOf("operation" to "agree"),
            keysTried = tried,
            aliasRuns = { alias -> check(agree(alias, service, own, peer).contentEquals(secret)) { "agrees_differently" } },
        )
    }

    // The operation holds doPhase; whether a second secret also needs one is read on its own instance, since a refusal there says nothing of the first order.
    private fun reset(service: ProbedService, own: KeyPair, peer: KeyPair): Map<String, Any> {
        val order = CallOrder(listOf("init"), { initialised(service.algorithm, service, own) }, listOf(CallStep("doPhase") { it.doPhase(peer.public, true); null }, CallStep("generateSecret") { it.generateSecret() }))
        val forward = LinkedHashMap(ResetRun.of(order))
        forward["withoutDoPhase"] = runCatching {
            val agreement = initialised(service.algorithm, service, own)
            agreement.doPhase(peer.public, true)
            if (agreement.generateSecret().contentEquals(agreement.generateSecret())) "same" else "different"
        }.getOrElse { "refused " + it.javaClass.simpleName }
        return mapOf("forward" to forward)
    }

    private fun agree(name: String, service: ProbedService, own: KeyPair, peer: KeyPair): ByteArray =
        initialised(name, service, own).run {
            doPhase(peer.public, true)
            generateSecret()
        }

    private fun initialised(name: String, service: ProbedService, own: KeyPair): KeyAgreement =
        KeyAgreement.getInstance(name, service.provider).apply { init(own.private) }

    private fun keyBits(service: ProbedService, key: ProbeKey): Map<String, Any> {
        val generator = service.keys.generatorOf(key) ?: return emptyMap()
        return Sweep.of(PairSizes.ALL) { bits ->
            val sized = service.keys.sized(key, bits, generator).getOrThrow()
            agree(service.algorithm, service, sized.pair!!, service.keys.peer(sized))
        }
    }

    private fun peerOfOtherSize(service: ProbedService, key: ProbeKey): Any? {
        if (!service.keys.sizable(key)) return null
        val generator = service.keys.generatorOf(key) ?: return null
        val peer = PairSizes.ALL.filter { it != key.bits }.firstNotNullOfOrNull { service.keys.sized(key, it, generator).getOrNull() } ?: return null
        val other = peer.bits ?: return null
        return linkedMapOf("peerBits" to other, "result" to (ErrorText.refusal { agree(service.algorithm, service, key.pair!!, peer.pair!!) } ?: "accepted"))
    }
}
