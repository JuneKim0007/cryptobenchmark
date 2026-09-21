package io.github.junekim0007.cryptobench.discovery.trial.call

import io.github.junekim0007.cryptobench.discovery.contract.ServiceKey

internal object DefaultCalls {

    private val CALLS: Map<String, DefaultCall> = mapOf(
        "Cipher" to CipherCall,
        "Signature" to SignatureCall,
        "Mac" to MacCall,
        "MessageDigest" to DigestCall,
        "KeyGenerator" to GeneratorCall(pair = false),
        "KeyPairGenerator" to GeneratorCall(pair = true),
        "KeyAgreement" to AgreementCall,
    ).mapKeys { (type, _) -> ServiceKey.fold(type) }

    fun of(type: String): DefaultCall? = CALLS[ServiceKey.fold(type)]
}
