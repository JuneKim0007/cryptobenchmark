package io.github.junekim0007.cryptobench.contract.capture

data class ServiceEntry(
    val type: String,
    val algorithm: String,
    val className: String = "",
    val aliases: List<String> = emptyList(),
    val attributes: ServiceAttributes = ServiceAttributes.empty(),
) {

    override fun toString(): String = "$type.$algorithm"
}
