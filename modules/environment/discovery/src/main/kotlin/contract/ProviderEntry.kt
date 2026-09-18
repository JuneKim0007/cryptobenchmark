package io.github.junekim0007.cryptobench.discovery.contract

/** One installed provider, at its position in the preference order. */
data class ProviderEntry(
    val name: String,
    /** 1-based position in Security.getProviders(), which is the order getInstance searches. */
    val precedence: Int,
    val version: String = "",
    val info: String = "",
    val services: List<ServiceEntry> = emptyList(),
    /** Aliases whose target service is not registered: recorded rather than silently dropped. */
    val unresolvedAliases: List<AliasEntry> = emptyList(),
) {

    init {
        require(precedence >= 1) { "precedence is 1-based, was $precedence" }
    }

    /** Registered but empty means present and unusable, as a Keystore provider without the hardware is. */
    val usable: Boolean get() = services.isNotEmpty()

    override fun toString(): String = "$precedence:$name"
}
