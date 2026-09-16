package io.github.junekim0007.cryptobench.discovery.capture

import io.github.junekim0007.cryptobench.discovery.ServiceKey

/** One service as the provider declares it: what it is, plus every alias and attribute it carries. */
data class ServiceEntry(
    val type: String,
    val algorithm: String,
    val className: String = "",
    val aliases: List<String> = emptyList(),
    val attributes: ServiceAttributes = ServiceAttributes.empty(),
) {

    override fun toString(): String = "$type.$algorithm"
}
