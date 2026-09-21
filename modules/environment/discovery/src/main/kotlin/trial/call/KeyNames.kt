package io.github.junekim0007.cryptobench.discovery.trial.call

internal object KeyNames {

    private val SIZE_SUFFIX = Regex("^(.+)_(\\d+)$")
    private val WITH = Regex("with", RegexOption.IGNORE_CASE)

    fun cipherCandidates(algorithm: String): List<Pair<String, Int?>> {
        val base = algorithm.substringBefore('/')
        val sized = SIZE_SUFFIX.find(base)?.let { match -> listOf(match.groupValues[1] to match.groupValues[2].toInt()) }.orEmpty()
        return (listOf(base to null) + sized + listOf(base.substringBefore('-') to null)).distinct()
    }

    fun cipherBase(algorithm: String): String = algorithm.substringBefore('/')

    fun signatureKey(algorithm: String): String {
        val parts = algorithm.split(WITH)
        val key = (if (parts.size > 1) parts.last() else algorithm).removeSuffix("inP1363Format")
        return if (key.equals("ECDSA", ignoreCase = true)) "EC" else key
    }

    fun agreementKey(algorithm: String): String = if (algorithm.equals("ECDH", ignoreCase = true)) "EC" else algorithm
}
