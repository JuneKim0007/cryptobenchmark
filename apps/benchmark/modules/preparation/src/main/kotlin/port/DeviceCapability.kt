package io.github.junekim0007.cryptobench.preparation.port

import io.github.junekim0007.cryptobench.document.catalogue.CatalogueOverlays
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyCandidate

interface DeviceCapability {

    fun providers(): List<String>

    fun check(provider: String, type: String, algorithm: String): Availability

    fun measuredKey(provider: String, type: String, algorithm: String): KeyCandidate? = null

    // the captured Android API level; null on a JVM
    val sdkInt: Int? get() = null

    val platform: String? get() = CatalogueOverlays.platform(sdkInt, null)
}
