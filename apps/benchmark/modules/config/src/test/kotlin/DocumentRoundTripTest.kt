package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.config.effective.EffectiveDocument
import io.github.junekim0007.cryptobench.config.effective.ReportDocument
import io.github.junekim0007.cryptobench.config.effective.dto.Report
import io.github.junekim0007.cryptobench.config.global.GlobalDocument
import io.github.junekim0007.cryptobench.config.inventory.InventoryDocument
import io.github.junekim0007.cryptobench.config.testset.TestSetDocument
import java.io.File
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test

class DocumentRoundTripTest {

    private val fixture = DocumentFixture()
    private val files = fixture.files
    private val codec = fixture.codec
    private val directory = fixture.directory
    private val inventory = fixture.inventory
    private val global = fixture.global
    private val testSet = fixture.testSet
    private val effective = fixture.effective

    @Test
    fun everyKindRoundTripsInFull() {
        val warned = effective.copy(warnings = listOf("override_matches_nothing: {name=X}"))
        assertEquals(inventory, files.at(File(directory, "inventory.yaml"), InventoryDocument).let { it.write(inventory); it.read() })
        // effective.yaml holds settings only: what the run noticed travels in report.yaml
        assertEquals(warned.copy(warnings = emptyList(), skipped = emptyList()),
            files.at(File(directory, "effective.yaml"), EffectiveDocument).let { it.write(warned); it.read() })
        val report = Report(warned.runId, warned.warnings, warned.skipped)
        assertEquals(report, files.at(File(directory, "report.yaml"), ReportDocument).let { it.write(report); it.read() })
        assertEquals(global, files.at(File(directory, "global.yaml"), GlobalDocument).let { it.write(global); it.read() })
        assertEquals(testSet, files.at(File(directory, "scope.yaml"), TestSetDocument).let { it.write(testSet); it.read() })
        val text = File(directory, "effective.yaml").readText()
        assertTrue(text, !text.contains("&id") && !text.contains("*id"))
    }

    @Test
    fun theFileLayerStampsAndChecksTheVersion() {
        val written = files.at(File(directory, "inventory.yaml"), InventoryDocument).write(inventory)
        assertTrue(written.readText().startsWith("schemaVersion: 1\n"))
        written.writeText(written.readText().replaceFirst("schemaVersion: 1", "schemaVersion: 9"))
        val refused = assertThrows(IllegalArgumentException::class.java) { files.at(written, InventoryDocument).read() }.message!!
        assertTrue(refused, refused.startsWith("unsupported_schema_version: inventory.yaml: 9"))
    }
}
