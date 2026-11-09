package io.github.junekim0007.cryptobench.benchmark

import io.github.junekim0007.cryptobench.benchmark.run.HostHarness
import io.github.junekim0007.cryptobench.benchmark.verify.CaseCheck
import io.github.junekim0007.cryptobench.benchmark.verify.known.KnownAnswerFile
import io.github.junekim0007.cryptobench.benchmark.verify.record.CheckFile
import io.github.junekim0007.cryptobench.benchmark.verify.record.RecordDiff
import io.github.junekim0007.cryptobench.preparation.measurement.Variant
import org.junit.Assert.assertEquals
import org.junit.Test
import io.github.junekim0007.cryptobench.files.FileNames
import java.nio.file.Files

class RecordDiffTest {

    private val check = CaseCheck(CaseCheck.oracles(KnownAnswerFile.read(CheckFixture.knownAnswers), CheckFixture.alone, HostHarness.ONCE), HostHarness.ONCE)

    private fun written(vararg variants: Variant): List<Map<String, Any>> {
        val file = Files.createTempDirectory("check").resolve(FileNames.CHECK_RESULT).toFile()
        CheckFile.write(file, variants.flatMap { listOf(check.check(CheckFixture.digest(it)), check.check(CheckFixture.gcmEncrypt(it))) }, mapOf("harness" to "test"))
        return CheckFile.cases(file)
    }

    @Test
    fun twoRunsOfTheSameCasesHaveNoDifference() {
        assertEquals(emptyList<String>(), RecordDiff.of(written(Variant.FIXED), written(Variant.FIXED)))
    }

    @Test
    fun everyAddedRemovedAndChangedFieldIsListed() {
        val baseline = written(Variant.FIXED, Variant.NOT_FIXED)
        val changed = baseline.map { case ->
            if (case["id"].toString().endsWith("_notFixed") && "GCM" in case["id"].toString()) case + ("outcome" to "fail") else case
        }.drop(1) + mapOf("id" to "new", "outcome" to "pass")
        val lines = RecordDiff.of(baseline, changed)
        assertEquals(3, lines.size)
        assertEquals(listOf("removed:", "added:", "changed:"), lines.map { it.substringBefore(' ') })
        assertEquals(true, lines.last().endsWith("outcome: pass -> fail"))
    }
}
