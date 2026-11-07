package io.github.junekim0007.cryptobench.discovery.trial.requirement

import io.github.junekim0007.cryptobench.discovery.contract.ServiceRequirement
import java.security.InvalidKeyException
import java.security.Key
import java.security.spec.AlgorithmParameterSpec
import javax.crypto.Mac
import javax.crypto.spec.IvParameterSpec
import javax.crypto.spec.SecretKeySpec

internal object MacFacts : RequirementCall {

    private val KEY_LENGTHS = (1..64) + (96..160 step 32)
    private val INPUTS = listOf(0, 1, 1 shl 20)

    override fun instance(service: ProbedService) {
        Mac.getInstance(service.algorithm, service.provider)
    }

    override fun measure(service: ProbedService, sheet: FactSheet): CallResult {
        val tried = mutableListOf<Map<String, Any>>()
        var detail = ""
        for (key in service.keys.of(service.type, service.algorithm, service.provider)) {
            if (key.secret == null) continue
            for ((_, spec) in listOf<Pair<String, AlgorithmParameterSpec?>>("" to null) + ParameterSpecs.candidates()) {
                val refused = runCatching { tag(service, key.secret, spec, ByteArray(8)) }.exceptionOrNull() ?: return measured(service, sheet, key, spec, tried)
                if (detail.isEmpty()) detail = ErrorText.of(refused)
            }
            tried += key.describe() + ("refused" to detail)
        }
        val reason = when {
            tried.isEmpty() -> ServiceRequirement.NO_KEY
            detail.startsWith(InvalidKeyException::class.java.simpleName) -> ServiceRequirement.KEY_REFUSED
            else -> ServiceRequirement.PARAMETERS_UNKNOWN
        }
        return CallResult(reason, detail, keysTried = tried)
    }

    private fun measured(service: ProbedService, sheet: FactSheet, key: ProbeKey, spec: AlgorithmParameterSpec?, tried: List<Map<String, Any>>): CallResult {
        val secret = key.secret!!
        val message = ParameterSpecs.random(64)
        val output = tag(service, secret, spec, message)
        sheet.measure("macBytes") { output.size }
        sheet.measure("lengthBeforeInit") { Mac.getInstance(service.algorithm, service.provider).macLength }
        sheet.measure("deterministic") { output.contentEquals(tag(service, secret, spec, message)) }
        if (key.isRawSecret) sheet.measure("keyBytes") { Sweep.of(KEY_LENGTHS) { tag(service, SecretKeySpec(ParameterSpecs.random(it), secret.algorithm), spec, ByteArray(8)) } }
        sheet.measure("withoutInit") { ErrorText.refusal { Mac.getInstance(service.algorithm, service.provider).doFinal(ByteArray(1)) } ?: "ok" }
        sheet.measure("ivSpec") { ErrorText.refusal { tag(service, secret, IvParameterSpec(ParameterSpecs.random(16)), ByteArray(1)) } ?: "ok" }
        sheet.measure("inputBytes") { Sweep.of(INPUTS) { tag(service, secret, spec, ByteArray(it)) } }
        sheet.measure("cloneable") { ErrorText.refusal { Mac.getInstance(service.algorithm, service.provider).clone() } ?: "ok" }
        sheet.measure("foreignKeys") { ForeignKeys.of(service, key) { other -> tag(service, other.secret!!, spec, ByteArray(8)) } }
        sheet.measure("reset") { mapOf("forward" to ResetRun.of(CallOrder(listOf("init"), { initialised(service.algorithm, service, secret, spec) }, listOf(CallStep("update") { mac -> mac.update(message); null }, CallStep("doFinal") { mac -> mac.doFinal() })))) }
        return CallResult(
            key = key,
            runWith = linkedMapOf<String, Any>("operation" to "mac").apply { spec?.let { put("spec", ParameterSpecs.describe(it)) } },
            keysTried = tried,
            aliasRuns = { alias -> check(tagAs(alias, service, secret, spec, message).contentEquals(output)) { "tags_differently" } },
            aliasAcceptsKey = { alias, other -> tagAs(alias, service, other.encrypting, spec, ByteArray(8)) },
        )
    }

    private fun tag(service: ProbedService, key: Key, spec: AlgorithmParameterSpec?, message: ByteArray): ByteArray =
        tagAs(service.algorithm, service, key, spec, message)

    private fun tagAs(name: String, service: ProbedService, key: Key, spec: AlgorithmParameterSpec?, message: ByteArray): ByteArray =
        initialised(name, service, key, spec).doFinal(message)

    private fun initialised(name: String, service: ProbedService, key: Key, spec: AlgorithmParameterSpec?): Mac =
        Mac.getInstance(name, service.provider).apply {
            if (spec == null) init(key) else init(key, spec)
        }
}
