package io.github.junekim0007.cryptobench.config.source

import io.github.junekim0007.cryptobench.document.versioned.DocumentReader
import io.github.junekim0007.cryptobench.settings.Facts

object FactsSource : DocumentReader<Facts> {

    override val schemaVersion: Int = Facts.SCHEMA_VERSION

    override fun parse(document: Map<String, Any>): Facts = Facts.read(document)
}
