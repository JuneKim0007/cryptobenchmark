import io.github.junekim0007.cryptobench.config.effective.ReportDocument
import io.github.junekim0007.cryptobench.config.effective.dto.Report
import io.github.junekim0007.cryptobench.config.yaml.YamlFiles
import io.github.junekim0007.cryptobench.preparation.report.SkipFile
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
import io.github.junekim0007.cryptobench.settings.Skip as ConfigSkip
import io.github.junekim0007.cryptobench.settings.Skip as PreparationSkip

/** Characterization: the same skips written by config (report.yaml) and preparation (skipped.yaml), and how each reads a skip without a stage. */
class SkipWritersTest {

    @get:Rule
    val folder = TemporaryFolder()

    private val fields = listOf(
        listOf("P", "Cipher", "AES/GCM/NoPadding", "no_match: 'quoted' and: colon"),
        listOf(null, "Mac", null, "path_not_applicable: x"),
        listOf(null, null, null, "multi\nline"),
    )

    @Test
    fun bothWriteEachSkipAsTheSameFlowMapping() {
        val config = YamlFiles().at(folder.root.resolve("c/report.yaml"), ReportDocument)
            .write(Report(null, skipped = fields.map { (p, t, n, r) -> ConfigSkip("stage", p, t, n, r!!) })).readText()
        val preparation = SkipFile(folder.newFolder("p"))
            .write(fields.map { (p, t, n, r) -> PreparationSkip("stage", p, t, n, r!!) }).readText()
        assertEquals(EXPECTED, "=== report.yaml\n$config=== skipped.yaml\n${preparation}end")
    }

    @Test
    fun todayConfigRefusesASkipWithoutAStageAndPreparationReadsItAsNull() {
        val text = "schemaVersion: 1\nskipped:\n- {reason: r}\n"
        val refused = assertThrows(IllegalArgumentException::class.java) {
            YamlFiles().at(folder.newFile("report.yaml").apply { writeText(text) }, ReportDocument).read()
        }
        assertEquals("report.yaml: missing_field: stage", refused.message)
        val directory = folder.newFolder("p")
        directory.resolve("skipped.yaml").writeText(text)
        assertEquals(listOf(PreparationSkip("null", reason = "r")), SkipFile(directory).read())
    }

    private companion object {
        val EXPECTED = """
            === report.yaml
            schemaVersion: 1
            warnings: []
            skipped:
            - {stage: stage, provider: P, type: Cipher, name: AES/GCM/NoPadding, reason: 'no_match:
                ''quoted'' and: colon'}
            - {stage: stage, type: Mac, reason: 'path_not_applicable: x'}
            - stage: stage
              reason: |-
                multi
                line
            === skipped.yaml
            schemaVersion: 1
            skipped:
            - {stage: stage, provider: P, type: Cipher, name: AES/GCM/NoPadding, reason: 'no_match:
                ''quoted'' and: colon'}
            - {stage: stage, type: Mac, reason: 'path_not_applicable: x'}
            - stage: stage
              reason: |-
                multi
                line
            end
        """.trimIndent()
    }
}
