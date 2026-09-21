package io.github.junekim0007.cryptobench.discovery

import io.github.junekim0007.cryptobench.discovery.contract.ServiceTrialEntry
import io.github.junekim0007.cryptobench.discovery.contract.TransformationTrialEntry
import io.github.junekim0007.cryptobench.discovery.contract.TrialOutcome
import io.github.junekim0007.cryptobench.discovery.contract.TrialReport
import io.github.junekim0007.cryptobench.discovery.write.TrialDocument
import io.github.junekim0007.cryptobench.discovery.write.YamlCodec
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

class TrialDocumentTest {

    private val report = TrialReport(
        capturedAtMillis = 1_700_000_000_000L,
        services = listOf(
            ServiceTrialEntry(
                provider = "SunJCE", type = "Cipher", algorithm = "AES", outcome = TrialOutcome.SUCCESS,
                transformations = listOf(
                    TransformationTrialEntry("AES/CTR/NoPadding", TrialOutcome.SUCCESS),
                    TransformationTrialEntry("AES/CTR/PKCS5Padding", TrialOutcome.failure("NoSuchAlgorithmException: CTR mode must be used with NoPadding")),
                ),
            ),
            ServiceTrialEntry(provider = "SunPKCS11", type = "KeyStore", algorithm = "PKCS11", outcome = TrialOutcome.failure("provider_not_installed")),
        ),
    )

    @Test
    fun roundTripsThroughYaml() {
        val codec = YamlCodec()
        assertEquals(report, TrialDocument.parse(codec.load(codec.dump(TrialDocument.of(report)))))
    }

    @Test
    fun rejectsAnotherSchemaVersion() {
        val document = LinkedHashMap(TrialDocument.of(report))
        document[TrialDocument.SCHEMA_VERSION] = TrialReport.SCHEMA_VERSION + 1
        val error = assertThrows(IllegalArgumentException::class.java) { TrialDocument.parse(document) }
        assertEquals("unsupported_schema_version: 2, this build reads 1", error.message)
    }

    @Test
    fun anOutcomeCarriesAnErrorExactlyWhenItFails() {
        assertThrows(IllegalArgumentException::class.java) { TrialOutcome(instantiates = true, error = "x") }
        assertThrows(IllegalArgumentException::class.java) { TrialOutcome(instantiates = false) }
    }
}
