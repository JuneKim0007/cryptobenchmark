package io.github.junekim0007.cryptobench.benchmark.preparation.source

import org.yaml.snakeyaml.DumperOptions
import org.yaml.snakeyaml.LoaderOptions
import org.yaml.snakeyaml.Yaml
import org.yaml.snakeyaml.constructor.SafeConstructor
import org.yaml.snakeyaml.representer.Representer

/** Read side only. A key written twice in a hand-edited file is an error, not "last one wins". */
internal class YamlCodec {

    @Suppress("UNCHECKED_CAST")
    fun load(text: String): Map<String, Any> {
        val dumperOptions = DumperOptions()
        val loaderOptions = LoaderOptions().apply { isAllowDuplicateKeys = false }
        return Yaml(SafeConstructor(loaderOptions), Representer(dumperOptions), dumperOptions, loaderOptions).load(text) as Map<String, Any>
    }
}
