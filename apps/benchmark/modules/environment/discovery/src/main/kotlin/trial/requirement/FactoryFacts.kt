package io.github.junekim0007.cryptobench.discovery.trial.requirement

import io.github.junekim0007.cryptobench.discovery.contract.ServiceRequirement
import javax.crypto.SecretKeyFactory
import javax.crypto.spec.SecretKeySpec

// The key path a password-based service runs on: does this factory make a key from a password, or only translate raw bytes.
internal object FactoryFacts : RequirementCall {

    private const val RAW_BYTES = 16

    override fun measure(service: ProbedService, sheet: FactSheet): CallResult {
        val password = service.keys.password(service.provider, service.algorithm)
        password.getOrNull()?.let { key ->
            sheet.measure("fromPassword") {
                linkedMapOf<String, Any>("keyAlgorithm" to key.encrypting.algorithm, "class" to key.encrypting.javaClass.name)
                    .apply { key.encrypting.encoded?.let { put("encodedBytes", it.size) } }
            }
            return CallResult(key = key, runWith = mapOf("operation" to "generateSecret", "spec" to "PBEKeySpec"))
        }
        val raw = ErrorText.refusal {
            SecretKeyFactory.getInstance(service.algorithm, service.provider).generateSecret(SecretKeySpec(ParameterSpecs.random(RAW_BYTES), service.algorithm))
        }
        sheet.measure("fromPasswordRefused") { ErrorText.of(password.exceptionOrNull()!!) }
        if (raw != null) return CallResult(ServiceRequirement.PARAMETERS_UNKNOWN, raw)
        return CallResult(runWith = mapOf("operation" to "generateSecret", "spec" to "SecretKeySpec"))
    }
}
