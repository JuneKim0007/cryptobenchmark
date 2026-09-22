package io.github.junekim0007.cryptobench.config.effective

import io.github.junekim0007.cryptobench.config.inventory.dto.Inventory
import io.github.junekim0007.cryptobench.config.inventory.dto.InventoryEntry
import io.github.junekim0007.cryptobench.config.testset.dto.Override
import io.github.junekim0007.cryptobench.config.testset.dto.Rule
import org.junit.Assert.assertEquals
import org.junit.Test

class OverrideResolverTest {

    private val gcm = Inventory.Located("SunJCE", "Cipher", "AES/GCM/NoPadding",
        InventoryEntry(runs = true, keySizes = listOf(256), providerChose = "GCM iv=12B"))

    /** Written in the "wrong" order on purpose: specificity decides, not position. */
    @Test
    fun theNarrowestRuleWinsAndListsReplace() {
        val resolver = OverrideResolver(listOf(
            Override(Rule(provider = "SunJCE", type = "Cipher", name = "AES/GCM/NoPadding"), keySizes = listOf(256)),
            Override(Rule(type = "Cipher"), keySizes = listOf(128), inputSizes = listOf(64)),
            Override(Rule(type = "Cipher", name = "AES/*"), keySizes = listOf(128, 192)),
        ))
        val entry = resolver.resolve(gcm, null)
        assertEquals(listOf(256), entry.keySizes)
        assertEquals(listOf(64), entry.inputSizes)
    }

    /** Whatever the provider still decides is named, so a comparison can see it. */
    @Test
    fun providerDefaultsAreNamed() {
        assertEquals(listOf("keySize", "parameters"), OverrideResolver(emptyList()).resolve(gcm, null).providerDefaults)
        val explicit = OverrideResolver(listOf(Override(Rule(name = "AES/GCM/NoPadding"), keySizes = listOf(128),
            parameters = mapOf("class" to "javax.crypto.spec.GCMParameterSpec", "arguments" to listOf(128, "fresh(12)")))))
        assertEquals(emptyList<String>(), explicit.resolve(gcm, null).providerDefaults)
    }

    /** DESede's default key encodes to 192 bits but init accepts only 112 or 168: the observation stays in the inventory. */
    @Test
    fun anObservedSizeIsNeverTurnedIntoAnArgument() {
        val desede = Inventory.Located("SunJCE", "Cipher", "DESede/CBC/PKCS5Padding", InventoryEntry(runs = true, keySizes = listOf(192)))
        val entry = OverrideResolver(emptyList()).resolve(desede, null)
        assertEquals(emptyList<Int>(), entry.keySizes)
        assertEquals(listOf("keySize"), entry.providerDefaults)
    }

    @Test
    fun aKeySpecLeavesNoSize() {
        val ec = Inventory.Located("SunEC", "Signature", "SHA256withECDSA", InventoryEntry(runs = true, keySizes = listOf(384)))
        val curve = mapOf("class" to "java.security.spec.ECGenParameterSpec", "arguments" to listOf("secp256r1"))
        val entry = OverrideResolver(listOf(Override(Rule(name = "SHA256withECDSA"), key = curve))).resolve(ec, null)
        assertEquals(emptyList<Int>(), entry.keySizes)
        assertEquals(curve, entry.key)
    }

    @Test
    fun operationsNarrowLikeAnyOtherValue() {
        val resolver = OverrideResolver(listOf(
            Override(Rule(type = "Cipher"), operations = listOf("ENCRYPT")),
            Override(Rule(name = "AES/GCM/NoPadding"), operations = listOf("DECRYPT")),
        ))
        assertEquals(listOf("DECRYPT"), resolver.resolve(gcm, null).operations)
        assertEquals(emptyList<String>(), OverrideResolver(emptyList()).resolve(gcm, null).operations)
    }

    /** A group is one primitive measured twice, so an override can name the group and leave the other alone. */
    @Test
    fun anOverrideCanNameOneGroup() {
        val resolver = OverrideResolver(listOf(
            Override(Rule(type = "KeyPairGenerator", name = "EC"), keySizes = listOf(256)),
            Override(Rule(type = "KeyPairGenerator", name = "EC", group = "p384"), keySizes = listOf(384)),
        ))
        val entry = Inventory.Located("SunEC", "KeyPairGenerator", "EC", InventoryEntry(runs = true))
        assertEquals(listOf(256), resolver.resolve(entry, null).keySizes)
        assertEquals(listOf(256), resolver.resolve(entry, "p256").keySizes)
        assertEquals(listOf(384), resolver.resolve(entry, "p384").keySizes)
    }
}
