package io.github.junekim0007.cryptobench.contract.capture

data class ProviderEntry(
    val name: String,
    val precedence: Int,
    val version: String = "",
    val services: List<ServiceEntry> = emptyList(),
    val origin: ProviderOrigin = ProviderOrigin.PLATFORM,
    val artifact: String = "",
) {

    init {
        require((origin == ProviderOrigin.BUNDLED) == artifact.isNotEmpty()) { "invalid: $name origin ${origin.key} with artifact '$artifact'" }
    }

    override fun toString(): String = "$precedence:$name"
}
