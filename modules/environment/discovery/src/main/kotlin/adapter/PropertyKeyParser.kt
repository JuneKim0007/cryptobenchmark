package io.github.junekim0007.cryptobench.discovery.adapter

/**
 * Decodes the grammar the JCA reserves inside a Provider property map, which is a plain
 * String-to-String table:
 *
 *     Provider.<field>                    provider metadata
 *     Alg.Alias.<engine>.<alias>          alias -> standard name
 *     <engine>.<algorithm> <attribute>    one attribute of one service
 *     <engine>.<algorithm>                the implementing class
 */
internal object PropertyKeyParser {

    private const val META_PREFIX = "Provider."
    private const val ALIAS_PREFIX = "Alg.Alias."

    fun classify(key: String?): PropertyKey {
        if (key == null) {
            return PropertyKey.Malformed
        }

        if (key.startsWith(META_PREFIX)) {
            val field = key.substring(META_PREFIX.length)
            return if (field.isEmpty()) PropertyKey.Malformed else PropertyKey.ProviderMeta(field)
        }

        if (key.startsWith(ALIAS_PREFIX)) {
            val remainder = key.substring(ALIAS_PREFIX.length)
            val separator = remainder.indexOf('.')
            return if (separator <= 0 || separator == remainder.length - 1) {
                PropertyKey.Malformed
            } else {
                PropertyKey.Alias(remainder.substring(0, separator), remainder.substring(separator + 1))
            }
        }

        val space = key.indexOf(' ')
        val serviceSection = if (space < 0) key else key.substring(0, space)
        val separator = serviceSection.indexOf('.')
        if (separator <= 0 || separator == serviceSection.length - 1) {
            return PropertyKey.Malformed
        }
        val type = serviceSection.substring(0, separator)
        val algorithm = serviceSection.substring(separator + 1)
        if (space < 0) {
            return PropertyKey.ServiceImpl(type, algorithm)
        }
        val attribute = key.substring(space + 1).trim()
        return if (attribute.isEmpty()) PropertyKey.Malformed else PropertyKey.Attribute(type, algorithm, attribute)
    }
}
