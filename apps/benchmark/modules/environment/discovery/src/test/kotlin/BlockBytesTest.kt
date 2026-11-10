package io.github.junekim0007.cryptobench.discovery

import io.github.junekim0007.cryptobench.discovery.contract.RequirementReport
import io.github.junekim0007.cryptobench.discovery.contract.ServiceRequirement
import io.github.junekim0007.cryptobench.discovery.write.ProbeDirectory
import io.github.junekim0007.cryptobench.discovery.write.RequirementYamlWriter
import io.github.junekim0007.cryptobench.discovery.write.YamlCodec
import org.junit.Assert.assertEquals
import org.junit.Test
import java.nio.file.Files

/** The bytes discovery's BLOCK codec writes today: a capture-shaped document and a streamed requirements file. The codec merge keeps them. */
class BlockBytesTest {

    @Test
    fun aCaptureShapedDocumentDumpsToTheseBytes() {
        val services = listOf(linkedMapOf("type" to "Cipher", "algorithm" to "AES/GCM/NoPadding", "aliases" to listOf("2.16.840.1.101.3.4.1.6")))
        val document = linkedMapOf(
            "schemaVersion" to 1,
            "capturedAtMillis" to 1_700_000_000_000L,
            "runtime" to linkedMapOf("sdkInt" to 37, "release" to "17", "javaVersion" to "0", "fingerprint" to "", "kernel" to null),
            "providers" to listOf(
                linkedMapOf("name" to "SunJCE", "version" to "25", "precedence" to 1, "services" to services, "attributes" to emptyMap<String, Any>()),
                // one instance named twice: this codec does not dereference, so it dumps an anchor and an alias
                linkedMapOf("name" to "Other", "version" to "1.0", "precedence" to 2, "services" to services, "attributes" to linkedMapOf("note" to "yes")),
            ),
        )
        assertEquals(CAPTURE, YamlCodec().dump(document))
    }

    @Test
    fun aRequirementsFileIsStreamedToTheseBytes() {
        val report = RequirementReport(1_700_000_000_000L, 1_700_000_000_500L, listOf(
            ServiceRequirement("SunJCE", "Cipher", "AES/GCM/NoPadding", ServiceRequirement.RUNNABLE, className = "com.sun.crypto.provider.AESCipher\$General"),
            ServiceRequirement("SunJCE", "Mac", "HmacSHA256", ServiceRequirement.NOT_RUNNABLE, reason = ServiceRequirement.NO_KEY),
        ), millis = 12)
        val file = RequirementYamlWriter(ProbeDirectory(Files.createTempDirectory("block").toFile())).write(report)
        assertEquals(REQUIREMENTS, file.readText())
    }

    private companion object {
        val CAPTURE = """
            schemaVersion: 1
            capturedAtMillis: 1700000000000
            runtime:
              sdkInt: 37
              release: '17'
              javaVersion: '0'
              fingerprint: ''
              kernel: null
            providers:
            - name: SunJCE
              version: '25'
              precedence: 1
              services: &id001
              - type: Cipher
                algorithm: AES/GCM/NoPadding
                aliases:
                - 2.16.840.1.101.3.4.1.6
              attributes: {}
            - name: Other
              version: '1.0'
              precedence: 2
              services: *id001
              attributes:
                note: 'yes'
        """.trimIndent() + "\n"

        val REQUIREMENTS = """
            schemaVersion: 1
            capturedAtMillis: 1700000000000
            deviceClockMillis: 1700000000500
            millis: 12
            keyCache:
              generated: 0
              refused: 0
              reused: 0
              generationMillis: 0
            services:
            - provider: SunJCE
              type: Cipher
              algorithm: AES/GCM/NoPadding
              className: com.sun.crypto.provider.AESCipher${'$'}General
              status: runnable
              millis: 0
            - provider: SunJCE
              type: Mac
              algorithm: HmacSHA256
              status: not_runnable
              reason: no_key
              millis: 0
        """.trimIndent() + "\n"
    }
}
