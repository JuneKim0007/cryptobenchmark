package io.github.junekim0007.cryptobench.discovery.write

import org.yaml.snakeyaml.DumperOptions
import org.yaml.snakeyaml.Yaml

class YamlCodec(private val options: DumperOptions = block()) {

    fun dump(document: Any): String = Yaml(options).dump(document)

    @Suppress("UNCHECKED_CAST")
    fun load(text: String): Map<String, Any> = Yaml(options).load(text) as Map<String, Any>

    companion object {

        fun block(): DumperOptions = DumperOptions().apply {
            defaultFlowStyle = DumperOptions.FlowStyle.BLOCK
            indent = 2
        }
    }
}
