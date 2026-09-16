package io.github.junekim0007.cryptobench.discovery

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertThrows
import org.junit.Test
import java.util.Locale

class ServiceKeyTest {

    @Test
    fun foldsWhicheverWayItIsBuilt() {
        assertEquals(ServiceKey("Cipher", "AES"), ServiceKey("cipher", "aes"))
        assertEquals(ServiceKey("Cipher", "AES").hashCode(), ServiceKey("CIPHER", "aes").hashCode())
        assertEquals("CIPHER.AES", ServiceKey("Cipher", "AES").toString())
    }

    @Test
    fun keepsTypeAndAlgorithmApart() {
        assertNotEquals(ServiceKey("Cipher", "AES"), ServiceKey("KeyGenerator", "AES"))
    }

    @Test
    fun rejectsMissingFields() {
        listOf("" to "AES", "Cipher" to "", " " to "AES", "Cipher" to " ").forEach { (type, algorithm) ->
            val thrown = assertThrows(ServiceKeyException::class.java) { ServiceKey(type, algorithm) }
            assertEquals(true, thrown.message!!.startsWith("missing_field: "))
        }
    }

    @Test
    fun foldsTheSameUnderATurkishLocale() {
        val original = Locale.getDefault()
        try {
            Locale.setDefault(Locale.forLanguageTag("tr"))
            assertEquals("CIPHER", ServiceKey.fold("Cipher"))
            assertEquals(ServiceKey("Cipher", "AES"), ServiceKey("cipher", "aes"))
        } finally {
            Locale.setDefault(original)
        }
    }
}
