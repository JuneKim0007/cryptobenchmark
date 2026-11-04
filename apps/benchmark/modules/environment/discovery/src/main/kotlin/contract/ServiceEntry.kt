package io.github.junekim0007.cryptobench.discovery.contract

data class ServiceEntry(
    val type: String,
    val algorithm: String,
    val className: String = "",
    val aliases: List<String> = emptyList(),
    val attributes: ServiceAttributes = ServiceAttributes.empty(),
) {

    override fun toString(): String = "$type.$algorithm"
}
