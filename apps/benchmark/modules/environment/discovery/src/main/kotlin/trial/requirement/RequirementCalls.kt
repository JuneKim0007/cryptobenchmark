package io.github.junekim0007.cryptobench.discovery.trial.requirement

import io.github.junekim0007.cryptobench.discovery.contract.ServiceKey

internal object RequirementCalls {

    private val CALLS: Map<String, RequirementCall> = mapOf(
        "Cipher" to CipherFacts,
        "Signature" to SignatureFacts,
        "Mac" to MacFacts,
        "MessageDigest" to DigestFacts,
        "KeyGenerator" to GeneratorFacts,
        "KeyPairGenerator" to GeneratorFacts,
        "KeyAgreement" to AgreementFacts,
        "SecretKeyFactory" to FactoryFacts,
    ).mapKeys { (type, _) -> ServiceKey.fold(type) }

    fun of(type: String): RequirementCall? = CALLS[ServiceKey.fold(type)]
}
