package io.github.junekim0007.cryptobench.preparation.port

import io.github.junekim0007.cryptobench.preparation.key.plan.KeyCandidate

interface DeviceCapability {

    fun providers(): List<String>

    fun check(provider: String, type: String, algorithm: String): Availability

    fun measuredKey(provider: String, type: String, algorithm: String): KeyCandidate? = null
}
