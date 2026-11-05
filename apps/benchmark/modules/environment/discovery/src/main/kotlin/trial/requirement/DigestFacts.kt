package io.github.junekim0007.cryptobench.discovery.trial.requirement

import io.github.junekim0007.cryptobench.discovery.contract.ServiceRequirement
import java.security.MessageDigest

internal object DigestFacts : RequirementCall {

    private val INPUTS = listOf(0, 1, 1 shl 20)
    private const val PREFIX_BYTES = 8

    override fun measure(service: ProbedService, sheet: FactSheet): CallResult {
        val message = ParameterSpecs.random(64)
        val output = runCatching { digest(service.algorithm, service, message) }
            .getOrElse { return CallResult(ServiceRequirement.OPERATION_REFUSED, ErrorText.of(it)) }
        sheet.measure("digestBytes") { output.size }
        sheet.measure("lengthDeclared") { MessageDigest.getInstance(service.algorithm, service.provider).digestLength }
        sheet.measure("deterministic") { output.contentEquals(digest(service.algorithm, service, message)) }
        sheet.measure("inputBytes") { Sweep.of(INPUTS) { digest(service.algorithm, service, ByteArray(it)) } }
        sheet.measure("cloneable") { ErrorText.refusal { MessageDigest.getInstance(service.algorithm, service.provider).clone() } ?: "ok" }
        sheet.measure("emptyInputPrefix") { digest(service.algorithm, service, ByteArray(0)).take(PREFIX_BYTES).joinToString("") { "%02x".format(it) } }
        return CallResult(
            runWith = mapOf("operation" to "digest"),
            aliasRuns = { alias -> check(digest(alias, service, message).contentEquals(output)) { "digests_differently" } },
        )
    }

    private fun digest(name: String, service: ProbedService, message: ByteArray): ByteArray =
        MessageDigest.getInstance(name, service.provider).digest(message)
}
