package io.github.junekim0007.cryptobench.discovery.contract

data class ProviderEntry(
    val name: String,
    val precedence: Int,
    val version: String = "",
    val info: String = "",
    val services: List<ServiceEntry> = emptyList(),
    val unresolvedAliases: List<AliasEntry> = emptyList(),
) {

    init {
        require(precedence >= 1) { "precedence is 1-based, was $precedence" }
    }

    val usable: Boolean get() = services.isNotEmpty()

    override fun toString(): String = "$precedence:$name"
}
