package io.github.junekim0007.cryptobench.discovery.setting

data class ProviderSetting(
    val name: String,
    val precedence: Int,
    val version: String = "",
    val services: List<ServiceSetting> = emptyList(),
) {

    private val lookup = ServiceLookup(services)

    val usable: Boolean get() = services.isNotEmpty()

    fun find(type: String, algorithmOrAlias: String): ServiceSetting? = lookup.find(type, algorithmOrAlias)
}
