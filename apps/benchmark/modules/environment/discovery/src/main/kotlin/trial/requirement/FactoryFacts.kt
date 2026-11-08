package io.github.junekim0007.cryptobench.discovery.trial.requirement

import io.github.junekim0007.cryptobench.jca.failure.ErrorText
import io.github.junekim0007.cryptobench.discovery.contract.ServiceRequirement
import javax.crypto.SecretKeyFactory
import javax.crypto.spec.SecretKeySpec

// The key path a password-based service runs on: does this factory make a key from a password, or only translate raw bytes.
internal object FactoryFacts : RequirementCall {

    private val RAW_BYTES = listOf(16, 24, 32, 8)

    override fun instance(service: ProbedService) {
        SecretKeyFactory.getInstance(service.algorithm, service.provider)
    }

    override fun measure(service: ProbedService, sheet: FactSheet): CallResult {
        val password = service.keys.password(service.provider, service.algorithm)
        password.getOrNull()?.let { key ->
            sheet.measure("fromPassword") {
                linkedMapOf<String, Any>("keyAlgorithm" to key.encrypting.algorithm, "class" to key.encrypting.javaClass.name)
                    .apply { key.encrypting.encoded?.let { put("encodedBytes", it.size) } }
            }
            return CallResult(key = key, runWith = mapOf("operation" to "generateSecret", "spec" to "PBEKeySpec"))
        }
        sheet.measure("fromPasswordRefused") { ErrorText.of(password.exceptionOrNull()!!) }
        val raw = Sweep.of(RAW_BYTES) {
            SecretKeyFactory.getInstance(service.algorithm, service.provider).generateSecret(SecretKeySpec(ParameterSpecs.random(it), service.algorithm))
        }
        sheet.measure("rawKeyBytes") { raw }
        if (raw["accepted"] == "") return CallResult(ServiceRequirement.PARAMETERS_UNKNOWN, raw["firstRefusal"].toString())
        return CallResult(runWith = mapOf("operation" to "generateSecret", "spec" to "SecretKeySpec"))
    }
}
