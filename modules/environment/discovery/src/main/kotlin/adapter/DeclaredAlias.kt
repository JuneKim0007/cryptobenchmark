package io.github.junekim0007.cryptobench.discovery.adapter

import io.github.junekim0007.cryptobench.discovery.contract.ServiceKey

internal data class DeclaredAlias(val type: String, val name: String, val target: String) {

    val targetKey: ServiceKey get() = ServiceKey(type, target)
}
