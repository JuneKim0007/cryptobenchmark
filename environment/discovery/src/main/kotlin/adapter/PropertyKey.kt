package io.github.junekim0007.cryptobench.discovery.adapter

/**
 * Restricted to 'discovery.probe' Package
 * One decoded key of a provider property map. Parsed by PropertyKeyParser, read by ProviderProbe,
 * then discarded: no PropertyKey ever reaches a capture.
 */
internal sealed class PropertyKey {

    object ProviderMeta : PropertyKey()
    object Malformed : PropertyKey()

    data class Alias(val type: String, val name: String) : PropertyKey()

    data class Attribute(val type: String, val algorithm: String, val name: String) : PropertyKey()

    data class ServiceImpl(val type: String, val algorithm: String) : PropertyKey()
}
