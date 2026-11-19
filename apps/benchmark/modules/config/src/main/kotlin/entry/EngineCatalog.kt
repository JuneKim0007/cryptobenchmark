package io.github.junekim0007.cryptobench.config.entry

import io.github.junekim0007.cryptobench.document.YamlCodec
import io.github.junekim0007.cryptobench.settings.EngineRows

/** setup-catalog.yaml from the classpath root, read once. */
object EngineCatalog {

    private const val RESOURCE = "/" + EngineRows.RESOURCE

    val rows: EngineRows by lazy {
        val text = EngineCatalog::class.java.getResource(RESOURCE)?.readText()
            ?: throw IllegalStateException("missing_resource: $RESOURCE is not on the classpath")
        EngineRows(YamlCodec.DOCUMENT.load(text))
    }
}
