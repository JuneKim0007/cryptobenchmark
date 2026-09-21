package io.github.junekim0007.cryptobench.discovery.write

import java.io.File
import java.io.IOException
import java.nio.file.FileAlreadyExistsException
import java.nio.file.Files
import java.nio.file.StandardOpenOption

class ProbeDirectory(val root: File) {

    fun create(name: String, text: String): File {
        if (!root.exists() && !root.mkdirs()) {
            throw IOException("cannot create ${root.absolutePath}")
        }
        val target = File(root, name)
        try {
            Files.write(target.toPath(), text.toByteArray(Charsets.UTF_8), StandardOpenOption.CREATE_NEW)
        } catch (exists: FileAlreadyExistsException) {
            throw FileAlreadyExistsException(target.path, null, "probe_exists: a capture is never overwritten; probe again after a second, or remove the file")
        }
        return target
    }
}
