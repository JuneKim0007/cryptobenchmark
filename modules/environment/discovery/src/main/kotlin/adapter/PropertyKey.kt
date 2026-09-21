package io.github.junekim0007.cryptobench.discovery.adapter

internal sealed class PropertyKey {

    object Malformed : PropertyKey()

    data class ProviderMeta(val field: String) : PropertyKey()

    data class Alias(val type: String, val name: String) : PropertyKey()

    data class Attribute(val type: String, val algorithm: String, val name: String) : PropertyKey()

    data class ServiceImpl(val type: String, val algorithm: String) : PropertyKey()
}
