package io.github.junekim0007.cryptobench.preparation.port

interface DeviceCapability {

    fun providers(): List<String>

    fun check(provider: String, type: String, algorithm: String): Availability
}
