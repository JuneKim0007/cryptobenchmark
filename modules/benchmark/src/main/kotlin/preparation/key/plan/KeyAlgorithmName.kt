package io.github.junekim0007.cryptobench.benchmark.preparation.key.plan

import io.github.junekim0007.cryptobench.benchmark.preparation.measurement.EngineTypeName

/** The algorithm a key is generated under, derived from the name the case passes to getInstance. */
internal object KeyAlgorithmName {

    private val CIPHER = EngineTypeName.fold("Cipher")
    private val SIGNATURE = EngineTypeName.fold("Signature")
    private val KEY_AGREEMENT = EngineTypeName.fold("KeyAgreement")

    private val WITH = Regex("with", RegexOption.IGNORE_CASE)

    fun of(type: String, algorithm: String): String = candidates(type, algorithm).first()

    /** Names to try in order: `ChaCha20-Poly1305` is keyed by `ChaCha20`, `AES_128/GCM/NoPadding` by `AES`. */
    fun candidates(type: String, algorithm: String): List<String> {
        val primary = primary(type, algorithm)
        if (EngineTypeName.fold(type) != CIPHER) {
            return listOf(primary)
        }
        return listOf(primary, primary.substringBefore('_'), primary.substringBefore('-')).distinct()
    }

    private fun primary(type: String, algorithm: String): String = when (EngineTypeName.fold(type)) {
        CIPHER -> algorithm.substringBefore('/')
        SIGNATURE -> signatureKey(algorithm)
        KEY_AGREEMENT -> if (algorithm.equals("ECDH", ignoreCase = true)) "EC" else algorithm
        else -> algorithm
    }

    private fun signatureKey(algorithm: String): String {
        val parts = algorithm.split(WITH)
        val key = if (parts.size > 1) parts.last() else algorithm
        return if (key.equals("ECDSA", ignoreCase = true)) "EC" else key
    }
}
