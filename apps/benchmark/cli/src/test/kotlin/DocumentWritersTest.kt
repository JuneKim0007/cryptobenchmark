import io.github.junekim0007.cryptobench.config.effective.ReportDocument
import io.github.junekim0007.cryptobench.config.effective.dto.Report
import io.github.junekim0007.cryptobench.settings.Skip
import io.github.junekim0007.cryptobench.config.yaml.YamlFiles
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFile
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder

/** The bytes of the host-reachable YAML writers, and that each writes through :document AtomicFile.
 * Not reachable on the host (androidTest only): ScopeInteropFile, CorePins, EnergyDryBenchmark, ScopeInputs. */
class DocumentWritersTest {

    @get:Rule
    val folder = TemporaryFolder()

    private val awkward = linkedMapOf<String, Any>(
        "schemaVersion" to 1,
        "line" to "a\nb",
        "colon" to "k: v",
        "quote" to "it's \"x\"",
        "empty" to "",
        "list" to listOf(1, 2.5, true),
        "nested" to linkedMapOf("emptyList" to emptyList<Any>(), "emptyMap" to emptyMap<String, Any>()),
    )

    @Test
    fun theBytesEachWriterWritesToday() {
        val document = DocumentFile.write(folder.root.resolve("d/document.yaml"), awkward).readText()
        val report = YamlFiles().at(folder.root.resolve("r/report.yaml"), ReportDocument).write(
            Report("run-1", listOf("w: one", "two\nlines"), listOf(Skip(Skip.CONFIG, "P", "Cipher", "AES", "no_match: x"), Skip(Skip.CONFIG, reason = "r"))),
        ).readText()
        assertEquals(EXPECTED, "=== DocumentFile\n$document=== YamlFile\n${report}end")
    }

    @Test
    fun bothWritersLeaveAStalePartialAloneAndLeaveNoneOfTheirOwn() {
        val stale = folder.newFile("report.yaml.partial").apply { writeText("stale") }
        YamlFiles().at(folder.root.resolve("report.yaml"), ReportDocument).write(Report(null))
        val other = folder.newFile(".document.yaml.123.partial").apply { writeText("stale") }
        DocumentFile.write(folder.root.resolve("document.yaml"), awkward)
        assertEquals(listOf("stale", "stale"), listOf(stale.readText(), other.readText()))
        assertEquals(listOf(".document.yaml.123.partial", "document.yaml", "report.yaml", "report.yaml.partial"), folder.root.list()!!.sorted())
    }

    private companion object {
        val EXPECTED = """
            === DocumentFile
            schemaVersion: 1
            line: |-
              a
              b
            colon: 'k: v'
            quote: it's "x"
            empty: ''
            list: [1, 2.5, true]
            nested:
              emptyList: []
              emptyMap: {}
            === YamlFile
            schemaVersion: 2
            runId: run-1
            warnings:
            - 'w: one'
            - |-
              two
              lines
            skipped:
            - {stage: config, provider: P, type: Cipher, name: AES, code: no_match, reason: x}
            - {stage: config, code: r}
            end
        """.trimIndent()
    }
}
