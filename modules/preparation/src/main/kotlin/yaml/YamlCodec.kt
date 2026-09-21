package io.github.junekim0007.cryptobench.preparation.yaml

import org.yaml.snakeyaml.DumperOptions
import org.yaml.snakeyaml.LoaderOptions
import org.yaml.snakeyaml.Yaml
import org.yaml.snakeyaml.constructor.SafeConstructor
import org.yaml.snakeyaml.representer.Representer

internal class YamlCodec {

    @Suppress("UNCHECKED_CAST")
    fun load(text: String): Map<String, Any> = yaml().load(text) as Map<String, Any>

    fun dump(document: Any): String = yaml().dump(document)

    private fun yaml(): Yaml {
        val dumperOptions = DumperOptions().apply {
            defaultFlowStyle = DumperOptions.FlowStyle.AUTO
            indent = 2
            isDereferenceAliases = true
        }
        val loaderOptions = LoaderOptions().apply { isAllowDuplicateKeys = false }
        return Yaml(SafeConstructor(loaderOptions), Representer(dumperOptions), dumperOptions, loaderOptions)
    }
}
