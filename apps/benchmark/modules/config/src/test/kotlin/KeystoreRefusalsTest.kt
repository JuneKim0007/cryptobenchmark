package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.config.effective.EffectiveBuilder
import io.github.junekim0007.cryptobench.config.global.GlobalDocument
import io.github.junekim0007.cryptobench.config.inventory.InventoryBuilder
import io.github.junekim0007.cryptobench.config.inventory.InventoryDocument
import io.github.junekim0007.cryptobench.config.source.CaptureSource
import io.github.junekim0007.cryptobench.config.source.TrialSource
import io.github.junekim0007.cryptobench.config.testset.TestSetDocument
import io.github.junekim0007.cryptobench.document.YamlCodec
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

/** A secure case the keystore trial refused is a config skip with the trial's code; a row the trial lacks keeps today's behaviour. */
class KeystoreRefusalsTest {

    private val codec = YamlCodec.DOCUMENT

    private val capture = """
        schemaVersion: 1
        capturedAtMillis: 1700000000000
        runtime: {model: Pixel 10, sdkInt: 37}
        providers:
        - {name: AndroidKeyStore, version: '1', precedence: 1, services: []}
    """.trimIndent()

    private fun born(type: String, name: String) = "- {provider: AndroidKeyStore, type: $type, algorithm: $name, instantiates: true, defaultRun: {works: false, error: 'IllegalStateException: no spec'}}\n"

    private val trial = """
        schemaVersion: 3
        capturedAtMillis: 1700000000000
        keystore:
          rows:
          - {provider: AndroidKeyStore, type: KeyPairGenerator, algorithm: RSA, backing: strongbox, keySize: 2048, supported: true, millis: 8000}
          - {provider: AndroidKeyStore, type: KeyPairGenerator, algorithm: RSA, backing: strongbox, keySize: 3072, supported: false, error: 'keystore_unsupported: KeyPairGenerator RSA/3072 strongbox: KeyStoreException: Unsupported key size', millis: 40}
          - {provider: AndroidKeyStore, type: KeyPairGenerator, algorithm: RSA, backing: tee, keySize: 3072, supported: true, millis: 2000}
          - {provider: AndroidKeyStore, type: KeyPairGenerator, algorithm: EC, backing: strongbox, curve: secp384r1, supported: false, error: 'keystore_unsupported: KeyPairGenerator EC/secp384r1 strongbox: InvalidAlgorithmParameterException: Unsupported StrongBox EC key size: 384 bits', millis: 5}
          - {provider: AndroidKeyStore, type: KeyPairGenerator, algorithm: XDH, backing: strongbox, supported: false, error: 'strongbox_unavailable: AndroidKeyStore strongbox: the device declares no android.hardware.strongbox_keystore', millis: 0}
        services:
    """.trimIndent() + "\n" + born("KeyPairGenerator", "RSA") + born("KeyPairGenerator", "EC") + born("KeyPairGenerator", "XDH") + born("KeyPairGenerator", "ED25519")

    private val inventory = InventoryBuilder().build(CaptureSource.parse(codec.load(capture)), TrialSource.parse(codec.load(trial)), InventoryBuilder.Files("probe_x.yaml", "trial_x.yaml"))

    private val testSet = """
        schemaVersion: 1
        description: secure key generation
        include:
        - {provider: AndroidKeyStore, type: KeyPairGenerator, name: RSA, variants: [secure]}
        - {provider: AndroidKeyStore, type: KeyPairGenerator, name: RSA, group: sb, variants: [secure]}
        - {provider: AndroidKeyStore, type: KeyPairGenerator, name: RSA, group: sbbig, variants: [secure]}
        - {provider: AndroidKeyStore, type: KeyPairGenerator, name: EC, group: sb, variants: [secure]}
        - {provider: AndroidKeyStore, type: KeyPairGenerator, name: EC, group: p256, variants: [secure]}
        - {provider: AndroidKeyStore, type: KeyPairGenerator, name: XDH, group: sb, variants: [secure]}
        - {provider: AndroidKeyStore, type: KeyPairGenerator, name: ED25519, variants: [secure]}
        overrides:
        - match: {provider: AndroidKeyStore, type: KeyPairGenerator, name: RSA}
          set: {keySizes: [3072, 4096]}
        - match: {provider: AndroidKeyStore, type: KeyPairGenerator, name: RSA, group: sb}
          set: {keySizes: [2048, 3072], key: {backing: strongbox}}
        - match: {provider: AndroidKeyStore, type: KeyPairGenerator, name: RSA, group: sbbig}
          set: {keySizes: [3072], key: {backing: strongbox}}
        - match: {provider: AndroidKeyStore, type: KeyPairGenerator, name: EC, group: sb}
          set: {key: {backing: strongbox, class: java.security.spec.ECGenParameterSpec, arguments: [secp384r1]}}
        - match: {provider: AndroidKeyStore, type: KeyPairGenerator, name: EC, group: p256}
          set: {key: {backing: strongbox, class: java.security.spec.ECGenParameterSpec, arguments: [secp256r1]}}
        - match: {provider: AndroidKeyStore, type: KeyPairGenerator, name: XDH, group: sb}
          set: {key: {backing: strongbox}}
    """.trimIndent()

    private val effective = EffectiveBuilder().build(GlobalDocument.parse(codec.load(Fixtures.seeded("schemaVersion: 1\nselection: {testSet: t.yaml}\n"))),
        TestSetDocument.parse(codec.load(testSet)), inventory, EffectiveBuilder.Files("global.yaml", "t.yaml", "inventory.yaml"))

    @Test
    fun aRefusedRowIsAConfigSkipWithTheTrialsCode() {
        assertEquals(listOf(
            "[config] AndroidKeyStore KeyPairGenerator RSA@sb: keystore_unsupported: KeyPairGenerator RSA/3072 strongbox: KeyStoreException: Unsupported key size",
            "[config] AndroidKeyStore KeyPairGenerator RSA@sbbig: keystore_unsupported: KeyPairGenerator RSA/3072 strongbox: KeyStoreException: Unsupported key size",
            "[config] AndroidKeyStore KeyPairGenerator EC@sb: keystore_unsupported: KeyPairGenerator EC/secp384r1 strongbox: InvalidAlgorithmParameterException: Unsupported StrongBox EC key size: 384 bits",
            "[config] AndroidKeyStore KeyPairGenerator XDH@sb: strongbox_unavailable: AndroidKeyStore strongbox: the device declares no android.hardware.strongbox_keystore",
        ), effective.skipped.map { it.toString() })
    }

    /** Refused sizes leave the entry; a whole refused entry is never written; a size or curve the trial has no row for stays as today. */
    @Test
    fun onlyTheRefusedSizesLeaveTheRun() {
        val written = effective.providers.getValue("AndroidKeyStore").getValue("KeyPairGenerator").mapValues { it.value.keySizes }
        assertEquals(mapOf("RSA" to listOf(3072, 4096), "RSA@sb" to listOf(2048), "EC@p256" to emptyList(), "ED25519" to emptyList()), written)
    }

    @Test
    fun theInventoryKeepsTheRowsAndATrialWithoutTheSectionIsRefused() {
        assertEquals(5, inventory.keystore.size)
        assertEquals(inventory, InventoryDocument.parse(InventoryDocument.of(inventory)))
        val older = trial.substringBefore("keystore:") + trial.substring(trial.indexOf("services:"))
        val refused = assertThrows(IllegalArgumentException::class.java) { TrialSource.parse(codec.load(older)) }
        assertEquals("missing_field: keystore", refused.message)
    }
}
