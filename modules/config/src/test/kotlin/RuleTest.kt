package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.config.testset.dto.Rule
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test

class RuleTest {

    @Test
    fun missingPartsMatchAnythingAndNamesIgnoreCase() {
        assertTrue(Rule(type = "cipher").matches("SunJCE", "Cipher", "AES"))
        assertTrue(Rule(name = "aes/cbc/pkcs5padding").matches("SunJCE", "Cipher", "AES/CBC/PKCS5PADDING"))
        assertFalse(Rule(provider = "BC").matches("SunJCE", "Cipher", "AES"))
    }

    @Test
    fun aStarMatchesAnyRunOfCharactersAndNothingElseIsSpecial() {
        assertTrue(Rule(name = "RSA/ECB/OAEP*").matches("SunJCE", "Cipher", "RSA/ECB/OAEPWithSHA-256AndMGF1Padding"))
        assertTrue(Rule(name = "*/GCM/*").matches("SunJCE", "Cipher", "AES_128/GCM/NoPadding"))
        assertFalse(Rule(name = "SHA-2.6").matches("SUN", "MessageDigest", "SHA-256"))
    }

    /** provider > exact name > name pattern > type: the order overrides are applied in. */
    @Test
    fun specificityOrdersFromBroadToNarrow() {
        val ordered = listOf(
            Rule(type = "Cipher"),
            Rule(type = "Cipher", name = "AES/*"),
            Rule(type = "Cipher", name = "AES/GCM/NoPadding"),
            Rule(provider = "SunJCE", type = "Cipher", name = "AES/*"),
        )
        assertEquals(ordered, ordered.shuffled(java.util.Random(1)).sortedBy { it.specificity })
    }

    @Test
    fun anEmptyRuleIsRefused() {
        assertEquals("empty_rule: give provider, type or name", assertThrows(IllegalArgumentException::class.java) { Rule() }.message)
    }
}
