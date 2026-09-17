import io.github.junekim0007.cryptobench.discovery.EnvironmentJsonWriter
import io.github.junekim0007.cryptobench.discovery.capture.RuntimeInfo
import io.github.junekim0007.cryptobench.discovery.probe.ProviderProbe
import io.github.junekim0007.cryptobench.discovery.setting.DiscoverySettingConverter
import java.io.File
import java.security.Provider
import java.security.Security

fun main(arguments: Array<String>) {
    val chosenProviderName = arguments.firstOrNull() ?: "SunJCE"
    val providers = Security.getProviders()

    section("Security.getProviders(), in preference order")
    providers.forEachIndexed { index, provider ->
        println("  %2d  %-22s %-8s %d services".format(
            index + 1, provider.name, provider.versionStr, provider.services.size))
    }

    val chosenProvider = Security.getProvider(chosenProviderName)
    if (chosenProvider == null) {
        println("\nno provider named '$chosenProviderName'; pass one of the names above")
        return
    }

    section("raw property map of $chosenProviderName, by shape")
    val propertyKeys = chosenProvider.stringPropertyNames().sorted()
    printShape(chosenProvider, propertyKeys, "Provider.<field>") { it.startsWith("Provider.") }
    printShape(chosenProvider, propertyKeys, "Alg.Alias.<engine>.<alias>") { it.startsWith("Alg.Alias.") }
    printShape(chosenProvider, propertyKeys, "<engine>.<algorithm> <attribute>") { isService(it) && it.contains(' ') }
    printShape(chosenProvider, propertyKeys, "<engine>.<algorithm>") { isService(it) && !it.contains(' ') }

    val capture = ProviderProbe().capture(providers, RuntimeInfo.ofDevice())
    val captured = capture.providers.first { it.name == chosenProviderName }

    section("what the probe made of $chosenProviderName")
    println("  precedence=${captured.precedence}  usable=${captured.usable}  " +
            "services=${captured.services.size}  unresolvedAliases=${captured.unresolvedAliases.size}")
    captured.services.filter { it.aliases.isNotEmpty() || !it.attributes.isEmpty }.take(3).forEach { service ->
        println("  ${service.type}.${service.algorithm}")
        println("      className = ${service.className}")
        println("      aliases   = ${service.aliases}")
        println("      modes     = ${service.attributes.supportedModes}")
        println("      paddings  = ${service.attributes.supportedPaddings}")
        println("      keySize   = ${service.attributes.keySize}")
    }

    val setting = DiscoverySettingConverter().convert(capture)
    section("the reduced discovery setting")
    println("  providers kept      = ${setting.providers.size}")
    println("  in-scope services   = ${setting.providers.sumOf { it.services.size }}")
    DiscoverySettingConverter.BENCHMARKED_TYPES.forEach { serviceType ->
        println("  %-18s %s".format(serviceType, setting.algorithms(serviceType).take(6)))
    }

    val target = File("build/playground/environment.json")
    EnvironmentJsonWriter().write(capture, target)
    section("wrote ${target.absolutePath} (${target.length()} bytes)")
}

private fun isService(key: String) = !key.startsWith("Provider.") && !key.startsWith("Alg.Alias.")

private fun section(title: String) = println("\n== $title")

private fun printShape(
    provider: Provider,
    propertyKeys: List<String>,
    label: String,
    matches: (String) -> Boolean,
) {
    val matching = propertyKeys.filter(matches)
    println("  $label  (${matching.size})")
    matching.take(3).forEach { key ->
        val value = provider.getProperty(key).let { if (it.length > 52) it.take(52) + "..." else it }
        println("      $key = $value")
    }
}
