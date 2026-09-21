package io.github.junekim0007.cryptobench.discovery.write

import org.yaml.snakeyaml.DumperOptions
import org.yaml.snakeyaml.Yaml

internal object YamlDocument {

    private val yaml = Yaml(DumperOptions().apply {
        defaultFlowStyle = DumperOptions.FlowStyle.BLOCK
        indent = 2
    })

    fun dump(document: Any): String = yaml.dump(document)

    @Suppress("UNCHECKED_CAST")
    fun load(text: String): Map<String, Any> = yaml.load(text) as Map<String, Any>
}
