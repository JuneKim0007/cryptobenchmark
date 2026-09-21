package io.github.junekim0007.cryptobench.config.yaml

import org.yaml.snakeyaml.DumperOptions
import org.yaml.snakeyaml.LoaderOptions
import org.yaml.snakeyaml.Yaml
import org.yaml.snakeyaml.constructor.SafeConstructor
import org.yaml.snakeyaml.representer.Representer

/**
 * A hand-edited file must not lose a line silently: a key written twice is an error, not "last one wins".
 * Shared values are written out in full, never as `&id001` anchors a reader has to chase.
 */
class YamlCodec {

    fun dump(document: Any): String = yaml().dump(document)

    @Suppress("UNCHECKED_CAST")
    fun load(text: String): Map<String, Any> = yaml().load(text) as Map<String, Any>

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
