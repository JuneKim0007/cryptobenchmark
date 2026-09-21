package io.github.junekim0007.cryptobench.discovery.write

import java.io.File
import java.io.IOException
import java.time.Instant
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter

internal object ProbeFile {

    private val STAMP: DateTimeFormatter =
        DateTimeFormatter.ofPattern("yyyyMMdd'T'HHmmss'Z'").withZone(ZoneOffset.UTC)

    fun name(prefix: String, capturedAtMillis: Long): String =
        prefix + "_" + STAMP.format(Instant.ofEpochMilli(capturedAtMillis)) + ".yaml"

    fun write(directory: File, name: String, text: String): File {
        if (!directory.exists() && !directory.mkdirs()) {
            throw IOException("cannot create ${directory.absolutePath}")
        }
        return File(directory, name).also { it.writeText(text, Charsets.UTF_8) }
    }
}
