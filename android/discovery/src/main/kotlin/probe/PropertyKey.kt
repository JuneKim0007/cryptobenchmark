package io.github.junekim0007.cryptobench.discovery.probe

import io.github.junekim0007.cryptobench.discovery.ServiceKey

/**
 * One classified key of a provider property map. A subclass carries only the parts its kind
 * guarantees, so there is no field that is meaningful for some kinds and null for others.
 */
internal sealed class PropertyKey {

    /** `Provider.id name` — never a service type. */
    object ProviderMeta : PropertyKey()

    /** No dot, or an empty part. */
    object Malformed : PropertyKey()

    /** `Alg.Alias.Cipher.RC4` = `ARC4` — [name] is the alias, the property value is the target. */
    data class Alias(val type: String, val name: String) : PropertyKey()

    /** `Cipher.AES SupportedModes` = `ECB|CBC` — [name] is the attribute. */
    data class Attribute(val type: String, val algorithm: String, val name: String) : PropertyKey() {
        val serviceKey: ServiceKey get() = ServiceKey.of(type, algorithm)
    }

    /** `Cipher.AES` — services are read from getServices(), so this is recorded and ignored. */
    data class ServiceImpl(val type: String, val algorithm: String) : PropertyKey()

    companion object {

        private const val META_PREFIX = "Provider."
        private const val ALIAS_PREFIX = "Alg.Alias."

        fun classify(key: String?): PropertyKey {
            if (key == null) {
                return Malformed
            }
            if (key.startsWith(META_PREFIX)) {
                return ProviderMeta
            }
            if (key.startsWith(ALIAS_PREFIX)) {
                val rest = key.substring(ALIAS_PREFIX.length)
                val dot = rest.indexOf('.')
                return if (dot <= 0 || dot == rest.length - 1) {
                    Malformed
                } else {
                    Alias(rest.substring(0, dot), rest.substring(dot + 1))
                }
            }
            val space = key.indexOf(' ')
            val head = if (space < 0) key else key.substring(0, space)
            val dot = head.indexOf('.')
            if (dot <= 0 || dot == head.length - 1) {
                return Malformed
            }
            val type = head.substring(0, dot)
            val algorithm = head.substring(dot + 1)
            if (space < 0) {
                return ServiceImpl(type, algorithm)
            }
            val attribute = key.substring(space + 1).trim()
            return if (attribute.isEmpty()) Malformed else Attribute(type, algorithm, attribute)
        }
    }
}
