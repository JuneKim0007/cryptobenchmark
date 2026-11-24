package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.document.catalogue.CatalogueOverlays
import io.github.junekim0007.cryptobench.document.catalogue.FamilyCatalogue
import io.github.junekim0007.cryptobench.document.catalogue.GroupExemplars
import io.github.junekim0007.cryptobench.preparation.peer.KeyUse
import io.github.junekim0007.cryptobench.preparation.port.Availability
import io.github.junekim0007.cryptobench.preparation.port.DeviceCapability
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

/** A generated key's use from a small catalogue and the shipped ones: exemplars then catalogue order, each by type Signature, Cipher, Mac, KeyAgreement, key type folded, Available on both providers, the type's timed operation from the entry's words. */
class KeyUseTest {

    private val cipher = """
        schemaVersion: 1
        family: cipher.secret
        algorithms:
          Cipher|AESWrap:
            key: {type: AES, origin: app, source: measured}
            operations: {value: [wrap, unwrap], source: measured}
          Cipher|AES/OnlyP:
            key: {type: AES, origin: app, source: measured}
            operations: {value: [encrypt, decrypt], source: measured}
          Cipher|AES:
            key: {type: aes, origin: app, source: measured}
            operations: {value: [encrypt, decrypt], source: measured}
          Cipher|NoKey:
            operations: {value: [encrypt, decrypt], source: measured}
    """.trimIndent()

    private val rest = """
        schemaVersion: 1
        family: mac.secret
        algorithms:
          Mac|HmacSHA256:
            key: {type: HMAC, origin: app, source: measured}
          Mac|AES-CMAC:
            key: {type: AES, origin: app, source: measured}
            operations: {value: [computeMac], source: measured}
          KeyAgreement|ECDH:
            key: {type: EC, origin: app, source: measured}
            operations: {value: [agree], source: measured}
    """.trimIndent()

    // P registers everything; Q lacks AES/OnlyP
    private val capability = object : DeviceCapability {
        override fun providers() = listOf("P", "Q")
        override fun check(provider: String, type: String, algorithm: String): Availability =
            if (provider == "Q" && algorithm == "AES/OnlyP") Availability.Unavailable("not_registered") else Availability.Available
    }

    private val uses = KeyUse(capability, FamilyCatalogue.parse(listOf(cipher, rest)))

    private fun picked(keyAlgorithm: String, consumer: String = "Q") =
        uses.of(keyAlgorithm, "P", consumer)?.let { "${it.type}|${it.algorithm} ${it.operation}" }

    @Test
    fun theFirstCatalogueEntryBothProvidersOfferWithATimedOperation() {
        assertEquals("Cipher|AES ENCRYPT", picked("AES"))
        assertEquals("Cipher|AES/OnlyP ENCRYPT", picked("AES", consumer = "P"))
        assertEquals("KeyAgreement|ECDH AGREE_KEY", picked("ec"))
        assertEquals("KeyAgreement|ECDH AGREE_KEY", picked("ECDSA"))
        assertNull(picked("HmacSHA256"))
        assertNull(picked("RSA"))
    }

    @Test
    fun macWordsMapToTheTypesOperation() {
        val macOnly = KeyUse(capability, FamilyCatalogue.parse(listOf(rest)))
        assertEquals("COMPUTE_MAC", macOnly.of("AES", "P", "Q")?.operation?.name)
    }

    @Test
    fun aDeviationSetsTheKeyTypeOnTheBuildsItNames() {
        val builds = """
            schemaVersion: 1
            builds:
              "P @ jdk-25": {name: P}
              "Q @ jdk-25": {name: Q}
        """.trimIndent()
        val deviations = """
            schemaVersion: 1
            deviations:
              d:
                builds: [P, Q]
                names: [Cipher|PBE]
                set: {key.type: AES}
        """.trimIndent()
        val pbe = """
            schemaVersion: 1
            family: cipher.secret
            algorithms:
              Cipher|PBE:
                key: {type: PBE, origin: app, source: measured}
                operations: {value: [encrypt, decrypt], source: measured}
                providers: {}
        """.trimIndent()
        val overlays = CatalogueOverlays.parse(builds, deviations)
        val jdk = object : DeviceCapability by capability {
            override val platform = "jdk-25"
        }
        assertEquals("ENCRYPT", KeyUse(jdk, FamilyCatalogue.parse(listOf(pbe), overlays)).of("AES", "P", "Q")?.operation?.name)
        assertNull(KeyUse(jdk, FamilyCatalogue.parse(listOf(pbe), overlays)).of("PBE", "P", "Q"))
        assertNull(KeyUse(jdk, FamilyCatalogue.parse(listOf(pbe))).of("AES", "P", "Q"))
    }

    // the shipped catalogues: every provider registers everything, no build (the base entries); groups.yaml's exemplars first
    private val shipped = KeyUse(capability)

    private fun generated(generator: String, name: String, keyAlgorithm: String) =
        shipped.of(generator, name, keyAlgorithm, "P", "Q").let { "${it.keyTypes.joinToString()} -> ${it.use}" }

    @Test
    fun theGeneratorsOwnEntryGivesTheKeyType() {
        assertEquals("HMAC -> Mac|HmacSHA256 COMPUTE_MAC", generated("KeyGenerator", "HmacSHA256", "HmacSHA256"))
        assertEquals("Ed25519 -> Signature|Ed25519 SIGN", generated("KeyPairGenerator", "Ed25519", "EdDSA"))
        assertEquals("X25519 -> KeyAgreement|X25519 AGREE_KEY", generated("KeyPairGenerator", "X25519", "XDH"))
        assertEquals("X448 -> KeyAgreement|X448 AGREE_KEY", generated("KeyPairGenerator", "x448", "XDH"))
        assertEquals("X25519 -> KeyAgreement|X25519 AGREE_KEY", generated("KeyPairGenerator", "OID.1.3.101.110", "XDH"))
    }

    @Test
    fun aKeyNamedOtherwiseThanItsGeneratorsType() {
        assertEquals("EC -> Signature|SHA256withECDSA SIGN", generated("KeyPairGenerator", "EC", "ECDSA"))
        assertEquals("EC -> Signature|SHA256withECDSA SIGN", generated("KeyPairGenerator", "ECDSA", "ECDSA"))
        assertEquals("X25519 -> KeyAgreement|X25519 AGREE_KEY", generated("KeyPairGenerator", "XDH", "XDH"))
        assertEquals("Ed25519 -> Signature|Ed25519 SIGN", generated("KeyPairGenerator", "EdDSA", "EdDSA"))
        assertEquals("XWING -> null", generated("KeyPairGenerator", "XWING", "XWING"))
        assertEquals("AES -> Cipher|AES/GCM/NoPadding ENCRYPT", generated("KeyGenerator", "Uncatalogued", "AES"))
    }

    @Test
    fun aKeyNameIsReadOnlyForAGeneratorWithNoEntry() {
        val kmac = KeyUse(lacking("KMAC128")).of("KeyGenerator", "KMAC128", "HMACSHA3-256", "P", "Q")
        assertEquals("KMAC128 -> null", "${kmac.keyTypes.joinToString()} -> ${kmac.use}")
    }

    private fun lacking(vararg names: String) = object : DeviceCapability by capability {
        override fun check(provider: String, type: String, algorithm: String): Availability =
            if (provider == "Q" && (type in names || algorithm in names)) Availability.Unavailable("not_registered") else Availability.Available
    }

    @Test
    fun exemplarsAcrossTypesInOrderSignatureCipherMacKeyAgreement() {
        assertEquals("Signature|SHA256withECDSA SIGN", shipped.of("EC", "P", "Q").toString())
        assertEquals("Signature|SHA256withRSA/PSS SIGN", shipped.of("RSA", "P", "Q").toString())
        assertEquals("Cipher|ECIES ENCRYPT", KeyUse(lacking("Signature")).of("EC", "P", "Q").toString())
        assertEquals("Cipher|SM2 ENCRYPT", KeyUse(lacking("Signature", "ECIES")).of("EC", "P", "Q").toString())
        assertEquals("KeyAgreement|ECDH AGREE_KEY", KeyUse(lacking("Signature", "Cipher")).of("EC", "P", "Q").toString())
        assertEquals("KeyAgreement|X25519 AGREE_KEY", shipped.of("X25519", "P", "Q").toString())
        assertEquals("Cipher|ECIES ENCRYPT", KeyUse(lacking("SHA256withECDSA")).of("EC", "P", "Q").toString())
        assertEquals("Cipher|RSA/ECB/PKCS1Padding ENCRYPT", KeyUse(lacking("SHA256withRSA/PSS")).of("RSA", "P", "Q").toString())
    }

    @Test
    fun catalogueOrderByTypeOnlyWhenNoExemplarFits() {
        assertEquals("Cipher|XIES ENCRYPT", KeyUse(capability, exemplars = GroupExemplars.parse("schemaVersion: 4\ngroups: {}")).of("X25519", "P", "Q").toString())
        assertEquals("Signature|NONEwithECDSA SIGN", KeyUse(lacking("SHA256withECDSA", "ECIES", "SM2", "ECDH")).of("EC", "P", "Q").toString())
    }
}
