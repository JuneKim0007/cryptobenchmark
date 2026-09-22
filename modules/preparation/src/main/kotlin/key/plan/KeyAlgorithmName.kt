package io.github.junekim0007.cryptobench.preparation.key.plan

import io.github.junekim0007.cryptobench.preparation.measurement.EngineTypeName

internal object KeyAlgorithmName {

    private val CIPHER = EngineTypeName.fold("Cipher")
    private val SIGNATURE = EngineTypeName.fold("Signature")
    private val KEY_AGREEMENT = EngineTypeName.fold("KeyAgreement")

    private val WITH = Regex("with", RegexOption.IGNORE_CASE)
    private val SIZE_SUFFIX = Regex("^(.+)_(\\d+)$")

    fun candidates(type: String, algorithm: String): List<KeyCandidate> {
        val primary = primary(type, algorithm)
        if (EngineTypeName.fold(type) != CIPHER) {
            return listOf(KeyCandidate(primary))
        }
        val sized = SIZE_SUFFIX.find(primary)?.let { match -> KeyCandidate(match.groupValues[1], match.groupValues[2].toInt()) }
        return listOfNotNull(KeyCandidate(primary), sized, KeyCandidate(primary.substringBefore('-'))).distinct()
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
