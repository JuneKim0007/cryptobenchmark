package io.github.junekim0007.cryptobench.discovery.write

import java.time.Instant
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter

internal object ProbeFileName {

    private val STAMP: DateTimeFormatter =
        DateTimeFormatter.ofPattern("yyyyMMdd'T'HHmmss'Z'").withZone(ZoneOffset.UTC)

    fun of(prefix: String, capturedAtMillis: Long): String =
        prefix + "_" + STAMP.format(Instant.ofEpochMilli(capturedAtMillis)) + ".yaml"
}
