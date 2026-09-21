package io.github.junekim0007.cryptobench.discovery

import io.github.junekim0007.cryptobench.discovery.write.ProbeDirectory
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test
import java.nio.file.FileAlreadyExistsException
import java.nio.file.Files

class ProbeDirectoryTest {

    private val directory = ProbeDirectory(Files.createTempDirectory("probe").resolve("nested").toFile())

    @Test
    fun createsTheDirectoryAndTheFile() {
        val target = directory.create("probe_x.yaml", "a: 1\n")
        assertEquals("a: 1\n", target.readText())
    }

    /** A capture is never replaced: a second write under the same name fails instead of truncating the first. */
    @Test
    fun refusesToOverwrite() {
        directory.create("probe_x.yaml", "first\n")
        val error = assertThrows(FileAlreadyExistsException::class.java) { directory.create("probe_x.yaml", "second\n") }
        assertTrue(error.message!!, error.message!!.endsWith("probe_exists: a capture is never overwritten; probe again after a second, or remove the file"))
        assertEquals("first\n", directory.root.resolve("probe_x.yaml").readText())
    }
}
