package io.github.junekim0007.cryptobench.discovery

import io.github.junekim0007.cryptobench.contract.trial.DefaultRunOutcome
import io.github.junekim0007.cryptobench.contract.trial.KeystoreRow
import io.github.junekim0007.cryptobench.contract.trial.KeystoreSection
import io.github.junekim0007.cryptobench.contract.trial.ServiceTrialEntry
import io.github.junekim0007.cryptobench.contract.trial.TransformationTrialEntry
import io.github.junekim0007.cryptobench.contract.trial.TrialOutcome
import io.github.junekim0007.cryptobench.contract.trial.TrialReport
import io.github.junekim0007.cryptobench.contract.trial.TriedKey
import io.github.junekim0007.cryptobench.contract.trial.TrialDocument
import io.github.junekim0007.cryptobench.discovery.write.ProbeDirectory
import io.github.junekim0007.cryptobench.discovery.write.TrialYamlWriter
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test
import java.nio.file.Files

class TrialDocumentTest {

    private val report = TrialReport(
        capturedAtMillis = 1_700_000_000_000L,
        services = listOf(
            ServiceTrialEntry(
                provider = "SunJCE", type = "Cipher", algorithm = "AES", outcome = TrialOutcome.SUCCESS,
                defaultRun = DefaultRunOutcome(works = true, keyAlgorithm = "AES", keyProvider = "SunJCE", keySize = 256, inputSize = 1024, bareName = true, keyMaterial = "exportable", keyFormat = "RAW",
                    triedKeys = listOf(TriedKey(128, "exportable", "RAW"), TriedKey(192, "non_exportable"), TriedKey(512, refused = true))),
                transformations = listOf(
                    TransformationTrialEntry("AES/CTR/NoPadding", TrialOutcome.SUCCESS, DefaultRunOutcome(works = true, providerChose = "ivBytes=16")),
                    TransformationTrialEntry("AES/CBC/NoPadding", TrialOutcome.SUCCESS, DefaultRunOutcome(works = false, inputSize = 32, error = "IllegalBlockSizeException: x")),
                    TransformationTrialEntry("AES/CTR/PKCS5Padding", TrialOutcome.failure("NoSuchAlgorithmException: CTR mode must be used with NoPadding")),
                ),
            ),
            ServiceTrialEntry(provider = "SunPKCS11", type = "KeyStore", algorithm = "PKCS11", outcome = TrialOutcome.failure("provider_not_installed")),
        ),
        keystore = KeystoreSection(listOf(
            KeystoreRow("AndroidKeyStore", "KeyPairGenerator", "RSA", KeystoreRow.STRONGBOX, keySize = 2048, supported = true, millis = 8000),
            KeystoreRow("AndroidKeyStore", "KeyPairGenerator", "EC", KeystoreRow.STRONGBOX, curve = "secp384r1", supported = false, error = "keystore_unsupported: x", millis = 3),
            KeystoreRow("AndroidKeyStore", "KeyPairGenerator", "XDH", KeystoreRow.TEE, supported = true),
        )),
    )

    @Test
    fun roundTripsThroughTheWrittenFile() {
        val folder = Files.createTempDirectory("trial").toFile()
        assertEquals(report, TrialDocument.read(TrialYamlWriter(ProbeDirectory(folder)).write(report)))
        folder.deleteRecursively()
    }

    @Test
    fun anAbsentKeystoreSectionKeepsItsReason() {
        val absent = report.copy(keystore = KeystoreSection(absent = "not_supported: no keystore"))
        val document = TrialDocument.of(absent)
        assertEquals(mapOf("absent" to "not_supported: no keystore"), document["keystore"])
        assertEquals(absent, TrialDocument.parse(document))
        assertThrows(IllegalArgumentException::class.java) { KeystoreRow("P", "KeyGenerator", "AES", "secure", supported = true) }
        assertThrows(IllegalArgumentException::class.java) { KeystoreSection(report.keystore!!.rows, absent = "x") }
    }

    /** An outcome carries an error exactly when it fails. */
    @Test
    fun refusesWhatCannotBeTrue() {
        assertThrows(IllegalArgumentException::class.java) { TrialOutcome(instantiates = true, error = "x") }
        assertThrows(IllegalArgumentException::class.java) { TrialOutcome(instantiates = false) }
    }
}
