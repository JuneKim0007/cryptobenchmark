import io.github.junekim0007.cryptobench.benchmark.check.EnergyCapability
import io.github.junekim0007.cryptobench.benchmark.report.energy.EnergyWindows
import io.github.junekim0007.cryptobench.config.source.CaptureSource
import io.github.junekim0007.cryptobench.document.versioned.YamlFiles
import io.github.junekim0007.cryptobench.contract.capture.CaptureDocument
import io.github.junekim0007.cryptobench.contract.requirements.RequirementDocument
import io.github.junekim0007.cryptobench.contract.trial.TrialDocument
import io.github.junekim0007.cryptobench.document.names.AlgorithmNames
import io.github.junekim0007.cryptobench.preparation.report.SkipFile
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
import java.io.File

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
        val file = folder.newFile("probe_x.yaml").apply { writeText("schemaVersion: 99\n") }
        val table = linkedMapOf(
            "document AlgorithmNames" to refusal { AlgorithmNames.read("schemaVersion: 99\n") },
            "config VersionedFile" to refusal { YamlFiles().readOnly(file, CaptureSource).read() },
            "preparation SkipFile" to refusal { SkipFile(folder.newFolder().apply { resolve("skipped.yaml").writeText("schemaVersion: 99\n") }).read() },
            "contract CaptureDocument" to refusal { CaptureDocument.read(file) },
            "contract TrialDocument" to refusal { TrialDocument.read(folder.newFile("trial_x.yaml").apply { writeText("schemaVersion: 99\n") }) },
            "contract RequirementDocument" to refusal { RequirementDocument.read(folder.newFile("requirements_x.yaml").apply { writeText("schemaVersion: 99\n") }) },
            "benchmark EnergyWindows" to refusal { EnergyWindows.read("{\"schemaVersion\": 99}") },
            "benchmark EnergyCapability" to refusal { EnergyCapability.parse("{\"schemaVersion\": 99}") },
        ).entries.joinToString("\n") { (reader, text) -> "$reader | $text" }
        assertEquals(EXPECTED, table)
    }

    private companion object {
        // reader | refusal
        val EXPECTED = """
            document AlgorithmNames | unsupported_schema_version: algorithm-names.yaml: 99, this build reads 1
            config VersionedFile | unsupported_schema_version: probe_x.yaml: 99, this build reads 1
            preparation SkipFile | unsupported_schema_version: skipped.yaml: 99, this build reads 2
            contract CaptureDocument | unsupported_schema_version: probe_x.yaml: 99, this build reads 1
            contract TrialDocument | unsupported_schema_version: trial_x.yaml: 99, this build reads 3
            contract RequirementDocument | unsupported_schema_version: requirements_x.yaml: 99, this build reads 1
            benchmark EnergyWindows | unsupported_schema_version: energy.json: 99, this build reads 3
            benchmark EnergyCapability | unsupported_schema_version: energy.yaml: 99, this build reads 3
        """.trimIndent()
    }
}
