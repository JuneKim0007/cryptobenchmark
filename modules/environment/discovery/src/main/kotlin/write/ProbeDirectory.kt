package io.github.junekim0007.cryptobench.discovery.write

import java.io.File
import java.io.IOException
import java.nio.file.FileAlreadyExistsException
import java.nio.file.Files
import java.nio.file.StandardOpenOption

class ProbeDirectory(val root: File) {

    private companion object {
        val STAMP = Regex("""\d{8}T\d{6}Z\.yaml""")
    }


    fun newest(prefix: String): File? =
        root.listFiles { file -> file.name.startsWith(prefix + "_") && file.name.endsWith(".yaml") }
            ?.filter { it.name.removePrefix(prefix + "_").matches(STAMP) }
            ?.maxByOrNull { it.name }

    fun named(prefix: String, stampedLike: File): File = File(root, prefix + "_" + stampedLike.name.substringAfterLast('_'))

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
