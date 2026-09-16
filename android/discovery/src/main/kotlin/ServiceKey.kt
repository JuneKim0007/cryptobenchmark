package io.github.junekim0007.cryptobench.discovery

import java.util.Locale

/**
 * A pair of JCA service 'type' and cryptography 'algorithm', normalized to UPPER CASE with respect
 * to the locale. A pair rather than one string because algorithm names contain '/', '.', ':' and
 * '#', so no flat id is safe.
 *
 * Normalizing happens in the constructor, not in a factory, so there is no way to build an
 * unnormalized key that then silently fails to match. Not a data class for the same reason: copy()
 * would bypass it.
 */
internal class ServiceKey(type: String, algorithm: String) {

    val type: String = fold(type)

    val algorithm: String = fold(algorithm)

    override fun equals(other: Any?): Boolean =
        other is ServiceKey && type == other.type && algorithm == other.algorithm

    override fun hashCode(): Int = 31 * type.hashCode() + algorithm.hashCode()

    override fun toString(): String = "$type.$algorithm"

    companion object {

        /**
         * Locale.ROOT or a Turkish-locale device folds "Cipher" to "CIPHER" with a dotted I and
         * stops matching. On Android the default locale is the user's, so this is not hypothetical.
         */
        fun fold(value: String): String = value.uppercase(Locale.ROOT)
    }
}
