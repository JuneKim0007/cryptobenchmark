package io.github.junekim0007.cryptobench.preparation.port

/** What preparation needs to know about the device, and nothing else; discovery is one way to answer it. */
interface DeviceCapability {

    /** Installed providers, in precedence order. */
    fun providers(): List<String>

    /** Whether this provider can serve this algorithm, as passed to getInstance, on this device. */
    fun check(provider: String, type: String, algorithm: String): Availability
}
