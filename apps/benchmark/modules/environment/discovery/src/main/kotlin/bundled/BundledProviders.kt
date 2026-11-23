package io.github.junekim0007.cryptobench.discovery.bundled

import io.github.junekim0007.cryptobench.contract.bundled.BundledProvider
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalSections

object BundledProviders {

    const val KEY = "bundledProviders"

    fun read(document: Map<String, Any>): List<BundledProvider> = BundledProvider.parseList(optionalSections(document, KEY), KEY)
}
