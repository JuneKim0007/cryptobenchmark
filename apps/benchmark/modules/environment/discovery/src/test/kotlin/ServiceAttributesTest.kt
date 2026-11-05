package io.github.junekim0007.cryptobench.discovery

import io.github.junekim0007.cryptobench.discovery.contract.ServiceAttributes
import org.junit.Assert.assertEquals
import org.junit.Test

class ServiceAttributesTest {

    /** Providers hand attributes over in hash order; a capture sorts them so two devices' files diff line by line. */
    @Test
    fun attributesAreSortedSoCapturesDiff() {
        val attributes = ServiceAttributes.of(linkedMapOf("SupportedPaddings" to listOf("NOPADDING"), "KeySize" to 256, "SupportedModes" to listOf("ECB")))
        assertEquals("{KeySize=256, SupportedModes=[ECB], SupportedPaddings=[NOPADDING]}", attributes.toString())
    }
}
