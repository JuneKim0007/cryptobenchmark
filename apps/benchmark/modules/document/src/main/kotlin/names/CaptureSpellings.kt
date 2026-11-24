package io.github.junekim0007.cryptobench.document.names

/** Per provider, in capture order, each service's registered name and the aliases the capture lists for it. */
data class CaptureSpellings(val services: Map<String, List<Service>>) {

    data class Service(val type: String, val name: String, val aliases: List<String>)

    private val byName = services.mapValues { (_, list) -> list.associateBy { it.type to AlgorithmNames.fold(it.name) } }

    fun aliasesOf(provider: String, type: String, name: String): List<String> =
        byName[provider]?.get(type to AlgorithmNames.fold(name))?.aliases.orEmpty()

    /** Whether the provider lists the spelling as an alias of one of its services of that type: what getInstance(spelling, provider) finds. */
    fun registers(provider: String, type: String, spelling: String): Boolean =
        services[provider].orEmpty().any { it.type == type && it.aliases.any { alias -> AlgorithmNames.fold(alias) == AlgorithmNames.fold(spelling) } }

    companion object {
        val NONE = CaptureSpellings(emptyMap())
    }
}
