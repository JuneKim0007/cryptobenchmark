package io.github.junekim0007.cryptobench.discovery

import io.github.junekim0007.cryptobench.discovery.adapter.ProviderProbe
import org.junit.Assert.assertEquals
import org.junit.Test
import java.security.Provider

class ProviderProbeTest {

    @Suppress("DEPRECATION")
    private val provider = object : Provider("Fake", 2.7, "a provider that registers nothing") {}

    /** Android's Provider has no getVersionStr(); the property map carries the same string on every platform. */
    @Test
    fun theVersionIsReadFromThePropertyMapNotFromGetVersionStr() {
        val entry = ProviderProbe().capture(arrayOf(provider)).providers.single()
        assertEquals("2.7", entry.version)
        assertEquals(provider.getProperty("Provider.id version"), entry.version)
    }
}
