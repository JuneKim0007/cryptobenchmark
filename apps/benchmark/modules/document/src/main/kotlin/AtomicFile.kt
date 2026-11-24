package io.github.junekim0007.cryptobench.document

import java.io.File
import java.io.IOException
import java.io.Writer
import java.nio.file.Files
import java.nio.file.StandardCopyOption

/** Whole or not at all: written to a unique temporary file beside the target, then renamed over it; when it must not exist, the target is first claimed by an exclusive create (a crash between claim and rename leaves it empty). */
object AtomicFile {

    fun write(file: File, text: String, replace: Boolean = true): File = write(file, replace) { it.write(text) }

    fun write(file: File, replace: Boolean = true, write: (Writer) -> Unit): File {
        val directory = file.absoluteFile.parentFile
        if (!directory.exists() && !directory.mkdirs()) {
            throw IOException("cannot create ${directory.absolutePath}")
        }
        val partial = File.createTempFile(".${file.name}.", ".partial", directory)
        var claimed = false
        var moved = false
        try {
            Files.newBufferedWriter(partial.toPath(), Charsets.UTF_8).use(write)
            // exclusive create is the no-overwrite step (FUSE refuses hard links)
            if (!replace) {
                Files.createFile(file.toPath())
                claimed = true
            }
            Files.move(partial.toPath(), file.toPath(), StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE)
            moved = true
        } finally {
            partial.delete()
            if (claimed && !moved) file.delete()
        }
        return file
    }
}
