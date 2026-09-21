import io.github.junekim0007.cryptobench.discovery.write.EnvironmentYamlWriter
import io.github.junekim0007.cryptobench.discovery.contract.RuntimeInfo
import io.github.junekim0007.cryptobench.discovery.adapter.ProviderProbe
import io.github.junekim0007.cryptobench.discovery.setting.DiscoverySettingConverter
import java.io.File
import java.security.Provider
import java.security.Security

fun main(arguments: Array<String>) {
    val chosenProviderName = arguments.firstOrNull() ?: "SunJCE"
    val providers = Security.getProviders()
    Security.getProviders().forEach { provider ->
        println(provider)
    }
    Security.getProviders().forEach { provider ->
    println("=== ${provider.name} ===")

    provider.forEach { (key, value) ->
        println("$key = $value")
    }
    
    section("Security.getProviders(), in preference order")
    providers.forEachIndexed { index, provider ->
    println("  %2d  %-22s %-8s %d services".format(
        index + 1, provider.name, provider.versionStr, provider.services.size))
    }
}

    section("registered names already in <algorithm>/<mode>/<padding> form")
    var threePartCount = 0
    Security.getProviders().forEach { provider ->
        provider.stringPropertyNames()
            .filterNot { it.startsWith("Provider.") || it.startsWith("Alg.Alias.") || it.contains(' ') }
            .forEach { key ->
                val engineType = key.substringBefore('.')
                val algorithm = key.substringAfter('.')
                if (algorithm.count { it == '/' } == 2) {
                    threePartCount++
                    if (threePartCount <= 8) println("  %-8s engine=%-8s algorithm=%s".format(provider.name, engineType, algorithm))
                }
            }
    }
    println("  $threePartCount registered names have the three-part form")

    section("the same text as a request string")
    listOf("AES/GCM/NoPadding", "AES/CBC/PKCS5Padding").forEach { transformation ->
        val registered = Security.getProviders().any { it.getService("Cipher", transformation) != null }
        println("  %-24s registered as a name: %-6s  accepted by getInstance: %s".format(
            transformation, registered,
            runCatching { javax.crypto.Cipher.getInstance(transformation) }.isSuccess))
    }


    // val chosenProvider = Security.getProvider(chosenProviderName)
    // if (chosenProvider == null) {
    //     println("\nno provider named '$chosenProviderName'; pass one of the names above")
    //     return
    // }

    // section("raw property map of $chosenProviderName, by shape")
    // val propertyKeys = chosenProvider.stringPropertyNames().sorted()
    // printShape(chosenProvider, propertyKeys, "Provider.<field>") { it.startsWith("Provider.") }
    // printShape(chosenProvider, propertyKeys, "Alg.Alias.<engine>.<alias>") { it.startsWith("Alg.Alias.") }
    // printShape(chosenProvider, propertyKeys, "<engine>.<algorithm> <attribute>") { isService(it) && it.contains(' ') }
    // printShape(chosenProvider, propertyKeys, "<engine>.<algorithm>") { isService(it) && !it.contains(' ') }

    // val capture = ProviderProbe().capture(providers, DeviceRuntimeReader.read())
    // val captured = capture.providers.first { it.name == chosenProviderName }

    // section("what the probe made of $chosenProviderName")
    // println("  precedence=${captured.precedence}  usable=${captured.usable}  " +
    //         "services=${captured.services.size}  unresolvedAliases=${captured.unresolvedAliases.size}")
    // captured.services.filter { it.aliases.isNotEmpty() || !it.attributes.isEmpty }.take(3).forEach { service ->
    //     println("  ${service.type}.${service.algorithm}")
    //     println("      className = ${service.className}")
    //     println("      aliases   = ${service.aliases}")
    //     println("      modes     = ${service.attributes.supportedModes}")
    //     println("      paddings  = ${service.attributes.supportedPaddings}")
    //     println("      keySize   = ${service.attributes.keySize}")
    // }

    // val setting = DiscoverySettingConverter().convert(capture)
    // section("the reduced discovery setting")
    // println("  providers kept      = ${setting.providers.size}")
    // println("  in-scope services   = ${setting.providers.sumOf { it.services.size }}")
    // BenchmarkScope.TYPES.forEach { serviceType ->
    //     println("  %-18s %s".format(serviceType, setting.algorithms(serviceType).take(6)))
    // }

    // val target = EnvironmentYamlWriter().write(capture, File("results/discovery"))
    // section("wrote ${target.absolutePath} (${target.length()} bytes)")
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
