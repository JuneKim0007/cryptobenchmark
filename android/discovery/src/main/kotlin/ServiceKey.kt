package io.github.junekim0007.cryptobench.discovery

import java.util.Locale

/** Composite because algorithm names contain '/', '.', ':' and '#', so no flat string id is safe. */
internal data class ServiceKey(val type: String, val algorithm: String) {

    override fun toString(): String = "$type.$algorithm"

    companion object {

        fun of(type: String, algorithm: String): ServiceKey = ServiceKey(fold(type), fold(algorithm))

        /**
         * Locale.ROOT or a Turkish-locale device folds "Cipher" to "CIPHER" with a dotted I and stops
         * matching. On Android the default locale is the user's, so this is not hypothetical.
         */
        fun fold(value: String): String = value.uppercase(Locale.ROOT)
    }
}
