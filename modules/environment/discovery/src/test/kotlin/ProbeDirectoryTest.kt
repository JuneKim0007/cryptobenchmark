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

    /** A capture is never replaced: a second write under the same name fails instead of truncating the first. */
    @Test
    fun createsTheDirectoryAndTheFileAndRefusesToOverwrite() {
        assertEquals("first\n", directory.create("probe_x.yaml", "first\n").readText())
        val error = assertThrows(FileAlreadyExistsException::class.java) { directory.create("probe_x.yaml", "second\n") }
        assertTrue(error.message!!, error.message!!.endsWith("probe_exists: a capture is never overwritten; probe again after a second, or remove the file"))
        assertEquals("first\n", directory.root.resolve("probe_x.yaml").readText())
    }
}
