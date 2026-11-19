package io.github.junekim0007.cryptobench.discovery.write

import io.github.junekim0007.cryptobench.document.AtomicFile
import io.github.junekim0007.cryptobench.files.StampedName
import java.io.File
import java.io.Writer
import java.nio.file.FileAlreadyExistsException

class ProbeDirectory(val root: File) {

    fun newest(prefix: String): File? =
        root.listFiles { file -> StampedName.isStamped(prefix, file.name) }?.maxByOrNull { it.name }

    fun named(prefix: String, stampedLike: File): File = File(root, StampedName.sibling(prefix, stampedLike.name))

    fun create(name: String, text: String): File = create(name) { it.write(text) }

    // Written as it is made: a requirements file with bundled providers is megabytes, and an API 26 heap is 48 MB.
    fun create(name: String, write: (Writer) -> Unit): File {
        val target = File(root, name)
        return try {
            AtomicFile.write(target, replace = false, write)
        } catch (exists: FileAlreadyExistsException) {
            throw FileAlreadyExistsException(target.path, null, "probe_exists: a capture is never overwritten; probe again after a second, or remove the file")
        }
    }
}
