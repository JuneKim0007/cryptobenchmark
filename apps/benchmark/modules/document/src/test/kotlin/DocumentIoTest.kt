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
    fun aRefusalWithoutACodeIsRefusedAsItIsAndADetailKeepsItsColons() {
        assertEquals("invalid: refusal without a code: x.yaml: precedence is 1-based, was 0", FileRefusal.of("x.yaml", "precedence is 1-based, was 0"))
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
    fun aWriteThatMustNotReplaceRefusesAnExistingFile() {
        val file = folder.newFile("c.yaml")
        assertThrows(FileAlreadyExistsException::class.java) { AtomicFile.write(file, "x", replace = false) }
        assertEquals("", file.readText())
    }

    @Test
    fun aQuotedScalarEscapesQuotesBackslashesAndNewlines() {
        assertEquals("\"a\\\"b\\\\c\\nd\"", YamlLine.quoted("a\"b\\c\nd"))
    }
}
