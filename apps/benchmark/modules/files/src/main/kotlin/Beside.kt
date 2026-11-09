package io.github.junekim0007.cryptobench.files

import java.io.File

/** A file named relative to another file: in its folder, or a value a settings file holds. */
object Beside {
    fun file(anchor: File, name: String): File = File(anchor.absoluteFile.parentFile, name)

    // The value a settings file names: an absolute value stands, anything else is beside that file.
    fun authored(settingsFile: File, value: String): File = File(value).let { if (it.isAbsolute) it else file(settingsFile, value) }
}
