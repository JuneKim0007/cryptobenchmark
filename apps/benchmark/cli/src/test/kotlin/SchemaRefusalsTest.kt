import io.github.junekim0007.cryptobench.benchmark.check.EnergyCapability
import io.github.junekim0007.cryptobench.benchmark.report.energy.EnergyWindows
import io.github.junekim0007.cryptobench.config.source.CaptureSource
import io.github.junekim0007.cryptobench.config.yaml.YamlFiles
import io.github.junekim0007.cryptobench.discovery.write.CaptureDocument
import io.github.junekim0007.cryptobench.discovery.write.RequirementDocument
import io.github.junekim0007.cryptobench.discovery.write.TrialDocument
import io.github.junekim0007.cryptobench.document.names.AlgorithmNames
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFile
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder

/** Every schemaVersion reader refuses version 99 with the one text of :document SchemaVersion. */
class SchemaRefusalsTest {

    @get:Rule
    val folder = TemporaryFolder()

    private fun refusal(read: () -> Any?): String = try {
        read()
        "accepted"
    } catch (refused: IllegalArgumentException) {
        refused.message!!
    }

    @Test
    fun everyReaderRefusesAnUnsupportedVersionWithOneText() {
        val wrong = mapOf<String, Any>("schemaVersion" to 99)
        val file = folder.newFile("probe_x.yaml").apply { writeText("schemaVersion: 99\n") }
        val table = linkedMapOf(
            "document AlgorithmNames" to refusal { AlgorithmNames.parse(wrong) },
            "config ReadOnlyYamlFile" to refusal { YamlFiles().readOnly(file, CaptureSource).read() },
            "preparation DocumentFile" to refusal { DocumentFile.read("skipped.yaml", "schemaVersion: 99\n", 1) },
            "discovery CaptureDocument" to refusal { CaptureDocument.parse(wrong) },
            "discovery TrialDocument" to refusal { TrialDocument.parse(wrong) },
            "discovery RequirementDocument" to refusal { RequirementDocument.parse(wrong) },
            "benchmark EnergyWindows" to refusal { EnergyWindows.read("{\"schemaVersion\": 99}") },
            "benchmark EnergyCapability" to refusal { EnergyCapability.parse("{\"schemaVersion\": 99}") },
        ).entries.joinToString("\n") { (reader, text) -> "$reader | $text" }
        assertEquals(EXPECTED, table)
    }

    private companion object {
        // reader | refusal
        val EXPECTED = """
            document AlgorithmNames | unsupported_schema_version: algorithm-names.yaml: 99, this build reads 1
            config ReadOnlyYamlFile | unsupported_schema_version: probe_x.yaml: 99, this build reads 1
            preparation DocumentFile | unsupported_schema_version: skipped.yaml: 99, this build reads 1
            discovery CaptureDocument | unsupported_schema_version: probe: 99, this build reads 1
            discovery TrialDocument | unsupported_schema_version: trial: 99, this build reads 3
            discovery RequirementDocument | unsupported_schema_version: requirements: 99, this build reads 1
            benchmark EnergyWindows | unsupported_schema_version: energy.json: 99, this build reads 3
            benchmark EnergyCapability | unsupported_schema_version: energy.yaml: 99, this build reads 3
        """.trimIndent()
    }
}
