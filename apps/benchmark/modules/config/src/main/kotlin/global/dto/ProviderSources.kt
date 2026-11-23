package io.github.junekim0007.cryptobench.config.global.dto

import io.github.junekim0007.cryptobench.contract.bundled.BundledProvider

data class ProviderSources(val bundled: List<BundledProvider> = emptyList())
