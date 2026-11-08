package io.github.junekim0007.cryptobench.discovery.trial.requirement

import io.github.junekim0007.cryptobench.jca.failure.Attempt
import io.github.junekim0007.cryptobench.jca.failure.ErrorText
import io.github.junekim0007.cryptobench.discovery.contract.ServiceRequirement
import java.security.MessageDigest

internal object DigestFacts : RequirementCall {

    private val INPUTS = listOf(0, 1, 1 shl 20)
    private val MESSAGE_SIZES = listOf(64, 32, 16, 1, 0)
    private const val PREFIX_BYTES = 8

    override fun instance(service: ProbedService) {
        MessageDigest.getInstance(service.algorithm, service.provider)
    }

    override fun measure(service: ProbedService, sheet: FactSheet): CallResult {
        // A digest can cap its input (HARAKA-256 takes 32 bytes): the longest message it takes is the base.
        var refused: Throwable? = null
        val (message, output) = MESSAGE_SIZES.map { ParameterSpecs.random(it) }.firstNotNullOfOrNull { message ->
            Attempt.of { message to digest(service.algorithm, service, message) }.onFailure { if (refused == null) refused = it }.getOrNull()
        } ?: return CallResult(ServiceRequirement.OPERATION_REFUSED, ErrorText.of(refused!!))
        sheet.measure("digestBytes") { output.size }
        sheet.measure("lengthDeclared") { MessageDigest.getInstance(service.algorithm, service.provider).digestLength }
        sheet.measure("deterministic") { output.contentEquals(digest(service.algorithm, service, message)) }
        sheet.measure("inputBytes") { Sweep.of(INPUTS) { digest(service.algorithm, service, ByteArray(it)) } }
        sheet.measure("cloneable") { ErrorText.refusal { MessageDigest.getInstance(service.algorithm, service.provider).clone() } ?: "ok" }
        sheet.measure("reset") { mapOf("forward" to ResetRun.of(CallOrder(emptyList(), { instance(service.algorithm, service) }, listOf(CallStep("update") { digest -> digest.update(message); null }, CallStep("digest") { digest -> digest.digest() })))) }
        sheet.measure("emptyInputPrefix") { digest(service.algorithm, service, ByteArray(0)).take(PREFIX_BYTES).joinToString("") { "%02x".format(it) } }
        return CallResult(
            runWith = mapOf("operation" to "digest", "inputBytes" to message.size),
            aliasRuns = { alias -> check(digest(alias, service, message).contentEquals(output)) { "digests_differently" } },
        )
    }

    private fun digest(name: String, service: ProbedService, message: ByteArray): ByteArray =
        instance(name, service).digest(message)

    private fun instance(name: String, service: ProbedService): MessageDigest = MessageDigest.getInstance(name, service.provider)
}
