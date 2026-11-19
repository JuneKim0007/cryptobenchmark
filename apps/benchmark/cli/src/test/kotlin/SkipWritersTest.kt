import io.github.junekim0007.cryptobench.config.effective.ReportDocument
import io.github.junekim0007.cryptobench.config.effective.dto.Report
import io.github.junekim0007.cryptobench.config.yaml.YamlFiles
import io.github.junekim0007.cryptobench.preparation.report.SkipFile
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
import io.github.junekim0007.cryptobench.settings.Skip

/** The same skips written by config (report.yaml) and preparation (skipped.yaml) and read back; a record without a code or of schema 1 is refused by both. */
class SkipWritersTest {

    @get:Rule
    val folder = TemporaryFolder()

    private val skips = listOf(
        Skip("stage", "P", "Cipher", "AES/GCM/NoPadding", "no_match: 'quoted' and: colon"),
        Skip("stage", null, "Mac", null, "path_not_applicable: x"),
        Skip("stage", reason = "check_failed: multi\nline", caseId = "Mac_HmacSHA1_x"),
        Skip("stage", reason = "bare_code"),
    )

    @Test
    fun bothWriteEachSkipAsTheSameFlowMapping() {
        val report = YamlFiles().at(folder.root.resolve("c/report.yaml"), ReportDocument)
        val config = report.write(Report(null, skipped = skips)).readText()
        val skipFile = SkipFile(folder.newFolder("p"))
        val preparation = skipFile.write(skips).readText()
        assertEquals(EXPECTED, "=== report.yaml\n$config=== skipped.yaml\n${preparation}end")
        assertEquals(skips, report.read().skipped)
        assertEquals(skips, skipFile.read())
    }

    @Test
    fun aRecordWithoutACodeOrOfTheOldSchemaIsRefusedByBoth() {
        fun refusals(text: String): List<String?> {
            val report = folder.newFolder().resolve("report.yaml").apply { writeText(text) }
            val directory = folder.newFolder().apply { resolve("skipped.yaml").writeText(text) }
            return listOf(assertThrows(IllegalArgumentException::class.java) { YamlFiles().at(report, ReportDocument).read() }.message,
                          assertThrows(IllegalArgumentException::class.java) { SkipFile(directory).read() }.message)
        }
        assertEquals(listOf("report.yaml: missing_field: skipped code", "missing_field: skipped code"),
                     refusals("schemaVersion: 2\nskipped:\n- {stage: s, reason: r}\n"))
        assertEquals(listOf("unsupported_schema_version: report.yaml: 1, this build reads 2", "unsupported_schema_version: skipped.yaml: 1, this build reads 2"),
                     refusals("schemaVersion: 1\nskipped: []\n"))
    }

    private companion object {
        val EXPECTED = """
            === report.yaml
            schemaVersion: 2
            warnings: []
            skipped:
            - {stage: stage, provider: P, type: Cipher, name: AES/GCM/NoPadding, code: no_match,
              reason: '''quoted'' and: colon'}
            - {stage: stage, type: Mac, code: path_not_applicable, reason: x}
            - stage: stage
              caseId: Mac_HmacSHA1_x
              code: check_failed
              reason: |-
                multi
                line
            - {stage: stage, code: bare_code}
            === skipped.yaml
            schemaVersion: 2
            skipped:
            - {stage: stage, provider: P, type: Cipher, name: AES/GCM/NoPadding, code: no_match,
              reason: '''quoted'' and: colon'}
            - {stage: stage, type: Mac, code: path_not_applicable, reason: x}
            - stage: stage
              caseId: Mac_HmacSHA1_x
              code: check_failed
              reason: |-
                multi
                line
            - {stage: stage, code: bare_code}
            end
        """.trimIndent()
    }
}
