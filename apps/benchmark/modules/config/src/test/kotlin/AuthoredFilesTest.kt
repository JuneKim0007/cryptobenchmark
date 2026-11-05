package io.github.junekim0007.cryptobench.config

import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
import java.io.File

class AuthoredFilesTest {

    @get:Rule
    val folder = TemporaryFolder()

    private fun global(text: String): File {
        File(folder.root, "set.yaml").writeText("schemaVersion: 1\ndescription: d\ninclude:\n  - {provider: '*'}\n")
        return folder.newFile("global.yaml").apply { writeText("schemaVersion: 1\nselection: {testSet: set.yaml}\n$text") }
    }

    private fun refused(text: String): String =
        assertThrows(IllegalArgumentException::class.java) { AuthoredFiles().read(global(text)) }.message!!

    @Test
    fun `a good file reads its test set and its bundled providers`() {
        val authored = AuthoredFiles().read(global("providers: {bundled: [{artifact: 'a:b:1', create: org.example.C}]}\n"))
        assertEquals("set.yaml", authored.testSetFile.name)
        assertEquals("a:b:1", authored.global.providers.bundled.single().artifact)
    }

    @Test
    fun `a typo key stops the read`() {
        val message = refused("rnu: {seed: 1}\n")
        assertTrue(message, message.contains("unknown_section"))
    }

    @Test
    fun `a missing test set is missing_file`() {
        val file = folder.newFile("other.yaml").apply { writeText("schemaVersion: 1\nselection: {testSet: nope.yaml}\n") }
        val message = assertThrows(IllegalArgumentException::class.java) { AuthoredFiles().read(file) }.message!!
        assertTrue(message, message.startsWith("missing_file"))
    }
}
