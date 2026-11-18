package io.github.junekim0007.cryptobench.discovery

import io.github.junekim0007.cryptobench.discovery.contract.DefaultRunOutcome
import io.github.junekim0007.cryptobench.discovery.contract.KeystoreRow
import io.github.junekim0007.cryptobench.discovery.contract.KeystoreSection
import io.github.junekim0007.cryptobench.discovery.contract.ServiceTrialEntry
import io.github.junekim0007.cryptobench.discovery.contract.TransformationTrialEntry
import io.github.junekim0007.cryptobench.discovery.contract.TrialOutcome
import io.github.junekim0007.cryptobench.discovery.contract.TrialReport
import io.github.junekim0007.cryptobench.discovery.contract.TriedKey
import io.github.junekim0007.cryptobench.discovery.write.TrialDocument
import io.github.junekim0007.cryptobench.document.YamlCodec
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

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
    fun roundTripsThroughYaml() {
        val codec = YamlCodec.CAPTURE
        assertEquals(report, TrialDocument.parse(codec.load(codec.dump(TrialDocument.of(report)))))
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

    /** Another schema is refused, and an outcome carries an error exactly when it fails. */
    @Test
    fun refusesWhatCannotBeTrue() {
        val document = LinkedHashMap(TrialDocument.of(report))
        document[TrialDocument.SCHEMA_VERSION] = TrialReport.SCHEMA_VERSION + 1
        val error = assertThrows(IllegalArgumentException::class.java) { TrialDocument.parse(document) }
        assertEquals("unsupported_schema_version", error.message!!.substringBefore(':'))
        assertThrows(IllegalArgumentException::class.java) { TrialOutcome(instantiates = true, error = "x") }
        assertThrows(IllegalArgumentException::class.java) { TrialOutcome(instantiates = false) }
    }
}
