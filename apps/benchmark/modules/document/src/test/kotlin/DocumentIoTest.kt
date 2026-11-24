package io.github.junekim0007.cryptobench.document

import io.github.junekim0007.cryptobench.document.versioned.DocumentReader
import io.github.junekim0007.cryptobench.document.versioned.FileRefusal
import io.github.junekim0007.cryptobench.document.versioned.YamlFiles
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
import java.io.File
import java.nio.file.FileAlreadyExistsException
import java.nio.file.NoSuchFileException
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit

class DocumentIoTest {

    @get:Rule
    val folder = TemporaryFolder()

    @Test
    fun aWrongOrMissingVersionIsOneRefusal() {
        val wrong = assertThrows(IllegalArgumentException::class.java) { SchemaVersion.require(mapOf("schemaVersion" to 99), 1, "x.yaml") }
        assertEquals("unsupported_schema_version: x.yaml: 99, this build reads 1", wrong.message)
        val missing = assertThrows(IllegalArgumentException::class.java) { SchemaVersion.require(emptyMap<String, Any>(), 1, "x.yaml") }
        assertEquals("missing_field: x.yaml: schemaVersion", missing.message)
    }

    @Test
    fun aParseRefusalNamesTheFileAfterItsCode() {
        val reader = object : DocumentReader<Unit> {
            override val schemaVersion = 1
            override fun parse(document: Map<String, Any>) = throw IllegalArgumentException("unknown_keys: run [sed]")
        }
        val refused = assertThrows(IllegalArgumentException::class.java) { YamlFiles().readOnly(File("x.yaml"), reader).read("schemaVersion: 1\n") }
        assertEquals("unknown_keys: x.yaml: run [sed]", refused.message)
    }

    @Test
    fun aDocumentThatIsNotAMappingIsRefusedNamingTheFile() {
        val reader = object : DocumentReader<Unit> {
            override val schemaVersion = 1
            override fun parse(document: Map<String, Any>) = Unit
        }
        listOf("", "- a\n- b\n").forEach { text ->
            val refused = assertThrows(IllegalArgumentException::class.java) { YamlFiles().readOnly(File("x.yaml"), reader).read(text) }
            assertEquals("not_a_mapping: x.yaml: the document is not a set of key: value entries", refused.message)
        }
    }

    @Test
    fun aRefusalWithoutACodeIsRefusedAsItIsAndADetailKeepsItsColons() {
        assertEquals("invalid: refusal without a code: x.yaml: count is negative, was -1", FileRefusal.of("x.yaml", "count is negative, was -1"))
        assertEquals("invalid: refusal without a code: x.yaml: ", FileRefusal.of("x.yaml", ""))
        assertEquals("invalid: refusal without a code: x.yaml: Oops: bad", FileRefusal.of("x.yaml", "Oops: bad"))
        assertEquals("wrong_type: x.yaml: c expects 'k: v'", FileRefusal.of("x.yaml", "wrong_type: c expects 'k: v'"))
    }

    @Test
    fun aWriteReplacesWholeAndLeavesNoTemporaryFile() {
        val file = folder.root.resolve("a/b.yaml")
        AtomicFile.write(file, "one\n")
        AtomicFile.write(file, "two\n")
        assertEquals("two\n", file.readText())
        assertEquals(listOf("b.yaml"), file.parentFile.list()!!.toList())
    }

    @Test
    fun aWriteThatMustNotReplaceRefusesAnExistingFileAndLeavesNoTemporaryFile() {
        val file = folder.root.resolve("c.yaml").apply { writeText("kept\n") }
        assertThrows(FileAlreadyExistsException::class.java) { AtomicFile.write(file, "x", replace = false) }
        assertEquals("kept\n", file.readText())
        assertEquals(listOf("c.yaml"), folder.root.list()!!.toList())
    }

    @Test
    fun aWriteThatMustNotReplaceWritesAFreshFileWhole() {
        val file = folder.root.resolve("d/e.yaml")
        AtomicFile.write(file, "fresh\n", replace = false)
        assertEquals("fresh\n", file.readText())
        assertEquals(listOf("e.yaml"), file.parentFile.list()!!.toList())
    }

    @Test
    fun aWriteThatFailsClaimsNothing() {
        val file = folder.root.resolve("f.yaml")
        assertThrows(IllegalStateException::class.java) { AtomicFile.write(file, replace = false) { error("boom") } }
        assertEquals(emptyList<String>(), folder.root.list()!!.toList())
    }

    // The writer removes its own partial, so the claim succeeds and the rename then fails with no test seam.
    @Test
    fun aRenameThatFailsAfterTheClaimReleasesTheClaim() {
        val file = folder.root.resolve("g.yaml")
        assertThrows(NoSuchFileException::class.java) {
            AtomicFile.write(file, replace = false) { folder.root.listFiles()!!.single { it.name.endsWith(".partial") }.delete() }
        }
        assertEquals(emptyList<String>(), folder.root.list()!!.toList())
        AtomicFile.write(file, "later\n", replace = false)
        assertEquals("later\n", file.readText())
    }

    @Test
    fun twoConcurrentWritesThatMustNotReplaceHaveExactlyOneWinner() {
        val file = folder.root.resolve("h.yaml")
        val start = CountDownLatch(1)
        val pool = Executors.newFixedThreadPool(2)
        val outcomes = listOf("a\n", "b\n").map { text ->
            pool.submit<Any> {
                start.await()
                try { AtomicFile.write(file, text, replace = false); text } catch (exists: FileAlreadyExistsException) { exists }
            }
        }
        start.countDown()
        val results = outcomes.map { it.get(10, TimeUnit.SECONDS) }
        pool.shutdown()
        val winners = results.filterIsInstance<String>()
        assertEquals(1, winners.size)
        assertEquals(1, results.filterIsInstance<FileAlreadyExistsException>().size)
        assertEquals(winners.single(), file.readText())
        assertEquals(listOf("h.yaml"), folder.root.list()!!.toList())
    }

    @Test
    fun aQuotedScalarEscapesQuotesBackslashesAndNewlines() {
        assertEquals("\"a\\\"b\\\\c\\nd\"", YamlLine.quoted("a\"b\\c\nd"))
    }
}
