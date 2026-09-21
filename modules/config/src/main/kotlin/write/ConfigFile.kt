package io.github.junekim0007.cryptobench.config.write

import java.io.File
import java.io.IOException
import java.nio.file.Files
import java.nio.file.StandardOpenOption

/** Always overwrites for now; keeping or merging a user's edits is #34. */
class ConfigFile(val directory: File, val name: String = DEFAULT_NAME) {

    val file: File get() = File(directory, name)

    fun write(text: String): File {
        if (!directory.exists() && !directory.mkdirs()) {
            throw IOException("cannot create ${directory.absolutePath}")
        }
        Files.write(file.toPath(), text.toByteArray(Charsets.UTF_8),
            StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING, StandardOpenOption.WRITE)
        return file
    }

    companion object {
        const val DEFAULT_NAME = "default.yaml"
    }
}
