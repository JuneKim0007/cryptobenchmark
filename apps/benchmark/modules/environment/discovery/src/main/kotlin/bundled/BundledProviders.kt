package io.github.junekim0007.cryptobench.discovery.bundled

import io.github.junekim0007.cryptobench.contract.bundled.BundledProvider
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalSections

object BundledProviders {

    // androidTest names the key through discovery, not contract
    const val KEY = BundledProvider.KEY

    fun read(document: Map<String, Any>): List<BundledProvider> = BundledProvider.parseList(optionalSections(document, KEY), KEY)
}
