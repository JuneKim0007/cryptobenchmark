package io.github.junekim0007.cryptobench.discovery.trial.requirement

import io.github.junekim0007.cryptobench.discovery.contract.ParameterReadBack
import io.github.junekim0007.cryptobench.discovery.contract.Attempt
import io.github.junekim0007.cryptobench.discovery.contract.ErrorText
import io.github.junekim0007.cryptobench.discovery.contract.ServiceRequirement
import java.security.InvalidKeyException
import java.security.PrivateKey
import java.security.PublicKey
import java.security.Signature
import java.security.spec.AlgorithmParameterSpec

internal object SignatureFacts : RequirementCall {

    private const val LENGTH_SAMPLES = 16
    private val INPUTS = listOf(0, 1, 1 shl 20)

    override fun instance(service: ProbedService) {
        Signature.getInstance(service.algorithm, service.provider)
    }

    override fun measure(service: ProbedService, sheet: FactSheet): CallResult {
        val tried = mutableListOf<Map<String, Any>>()
        var detail = ""
        for (key in service.keys.of(service.type, service.algorithm, service.provider, pairsOnly = true)) {
            for ((_, spec) in listOf<Pair<String, AlgorithmParameterSpec?>>("" to null) + ParameterSpecs.candidates()) {
                val message = ParameterSpecs.random(64)
                val refused = Attempt.of { sign(service, key.pair!!.private, spec, message) }.exceptionOrNull() ?: return measured(service, sheet, key, spec, message, tried)
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

    private fun measured(service: ProbedService, sheet: FactSheet, key: ProbeKey, spec: AlgorithmParameterSpec?, message: ByteArray, tried: List<Map<String, Any>>): CallResult {
        val private = key.pair!!.private
        val public = key.pair.public
        val signature = sign(service, private, spec, message)
        val deterministic = signature.contentEquals(sign(service, private, spec, message))
        sheet.measure("signatureBytes") { signature.size }
        sheet.measure("deterministic") { deterministic }
        if (!deterministic) sheet.measure("signatureBytesRange") { (0 until LENGTH_SAMPLES).map { sign(service, private, spec, message).size }.let { "${it.min()}-${it.max()}" } }
        sheet.measure("parameters") { parameters(service, private, spec) }
        sheet.measure("verifies") { verify(service.algorithm, service, public, spec, message, signature) }
        sheet.measure("tamperedSignature") { tampered(service, public, spec, message, signature) }
        sheet.measure("tamperedMessage") { verify(service.algorithm, service, public, spec, message.reversedArray(), signature) }
        sheet.measure("inputBytes") { Sweep.of(INPUTS) { sign(service, private, spec, ByteArray(it)) } }
        sheet.measure("setParameter") { setParameter(service, private) }
        if (service.keys.sizable(key)) sheet.measure("keyBits") { keyBits(service, key, spec) }
        sheet.measure("foreignKeys") { ForeignKeys.of(service, key) { other -> sign(service, other.pair!!.private, spec, message) } }
        sheet.measure("reset") { reset(service, private, public, spec, message, signature) }
        return CallResult(
            key = key,
            runWith = linkedMapOf<String, Any>("operation" to "sign", "inputBytes" to message.size).apply { spec?.let { put("spec", ParameterReadBack.describe(it)) } },
            keysTried = tried,
            aliasRuns = { alias -> check(verify(alias, service, public, spec, message, signature)) { "verifies_differently" } },
        )
    }

    private fun reset(service: ProbedService, private: PrivateKey, public: PublicKey, spec: AlgorithmParameterSpec?, message: ByteArray, signature: ByteArray): Map<String, Any> {
        val setParameter = listOfNotNull(spec?.let { "setParameter" })
        val forward = CallOrder(listOf("initSign") + setParameter, { signing(service, private, spec) }, listOf(CallStep("update") { it.update(message); null }, CallStep("sign") { it.sign() }))
        val reverse = CallOrder(listOf("initVerify") + setParameter, { verifying(service.algorithm, service, public, spec) }, listOf(CallStep("update") { it.update(message); null }, CallStep("verify") { byteArrayOf(if (it.verify(signature)) 1 else 0) }))
        return linkedMapOf(
            "forward" to ResetRun.of(forward) { _, output -> verify(service.algorithm, service, public, spec, message, output) },
            "reverse" to ResetRun.of(reverse),
        )
    }

    private fun sign(service: ProbedService, key: PrivateKey, spec: AlgorithmParameterSpec?, message: ByteArray): ByteArray =
        signing(service, key, spec).run {
            update(message)
            sign()
        }

    private fun signing(service: ProbedService, key: PrivateKey, spec: AlgorithmParameterSpec?): Signature =
        Signature.getInstance(service.algorithm, service.provider).apply {
            initSign(key)
            spec?.let { setParameter(it) }
        }

    private fun verify(name: String, service: ProbedService, key: PublicKey, spec: AlgorithmParameterSpec?, message: ByteArray, signature: ByteArray): Boolean =
        verifying(name, service, key, spec).run {
            update(message)
            verify(signature)
        }

    private fun verifying(name: String, service: ProbedService, key: PublicKey, spec: AlgorithmParameterSpec?): Signature =
        Signature.getInstance(name, service.provider).apply {
            initVerify(key)
            spec?.let { setParameter(it) }
        }

    private fun tampered(service: ProbedService, key: PublicKey, spec: AlgorithmParameterSpec?, message: ByteArray, signature: ByteArray): String {
        val bad = signature.clone()
        bad[bad.size / 2] = (bad[bad.size / 2].toInt() xor 1).toByte()
        return Attempt.of { verify(service.algorithm, service, key, spec, message, bad).toString() }.getOrElse { "refused " + it.javaClass.simpleName }
    }

    private fun parameters(service: ProbedService, key: PrivateKey, spec: AlgorithmParameterSpec?): Map<String, Any>? {
        val signature = Signature.getInstance(service.algorithm, service.provider)
        signature.initSign(key)
        spec?.let { signature.setParameter(it) }
        val parameters = signature.parameters ?: return null
        return ParameterReadBack.readable(parameters)?.let { ParameterReadBack.describe(it) } ?: mapOf("algorithm" to parameters.algorithm)
    }

    private fun setParameter(service: ProbedService, key: PrivateKey): Map<String, Any> {
        val accepted = ParameterSpecs.candidates().filter { (_, spec) ->
            ErrorText.refusal { Signature.getInstance(service.algorithm, service.provider).run { initSign(key); setParameter(spec) } } == null
        }
        return mapOf("accepted" to accepted.map { it.first })
    }

    private fun keyBits(service: ProbedService, key: ProbeKey, spec: AlgorithmParameterSpec?): Map<String, Any> {
        val generator = service.keys.generatorOf(key) ?: return emptyMap()
        return Sweep.of(PairSizes.ALL) { bits ->
            sign(service, service.keys.sized(key, bits, generator).getOrThrow().pair!!.private, spec, ByteArray(16))
        }
    }
}
