package io.github.junekim0007.cryptobench.document

import java.io.File
import java.io.IOException
import java.io.Writer
import java.nio.file.Files
import java.nio.file.StandardCopyOption

/** Whole or not at all: written to a unique temporary file beside the target, then renamed over it, or linked when it must not exist. */
object AtomicFile {

    fun write(file: File, text: String, replace: Boolean = true): File = write(file, replace) { it.write(text) }

    fun write(file: File, replace: Boolean = true, write: (Writer) -> Unit): File {
        val directory = file.absoluteFile.parentFile
        if (!directory.exists() && !directory.mkdirs()) {
            throw IOException("cannot create ${directory.absolutePath}")
        }
        val partial = File.createTempFile(".${file.name}.", ".partial", directory)
        try {
            Files.newBufferedWriter(partial.toPath(), Charsets.UTF_8).use(write)
            // a rename replaces silently; a hard link fails when the target exists, so it is the one atomic no-overwrite step
            if (replace) Files.move(partial.toPath(), file.toPath(), StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE)
            else Files.createLink(file.toPath(), partial.toPath())
        } finally {
            partial.delete()
        }
        return file
    }
}
